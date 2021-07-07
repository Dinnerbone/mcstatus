import asyncio

from mock import patch, Mock
import pytest

from mcstatus.protocol.connection import Connection, TCPAsyncSocketConnection
from mcstatus.server import MinecraftServer


class MockProtocolFactory(asyncio.Protocol):
    transport: asyncio.Transport

    def __init__(self, data_expected_to_receive, data_to_respond_with):
        self.data_expected_to_receive = data_expected_to_receive
        self.data_to_respond_with = data_to_respond_with

    def connection_made(self, transport):
        print("connection_made")
        self.transport = transport

    def connection_lost(self, exc):
        print("connection_lost")
        self.transport.close()

    def data_received(self, data):
        assert self.data_expected_to_receive in data
        self.transport.write(self.data_to_respond_with)

    def eof_received(self):
        print("eof_received")

    def pause_writing(self):
        print("pause_writing")

    def resume_writing(self):
        print("resume_writing")


@pytest.fixture()
async def create_mock_packet_server(event_loop):
    servers = []

    async def create_server(port, data_expected_to_receive, data_to_respond_with):
        server = await event_loop.create_server(
            lambda: MockProtocolFactory(data_expected_to_receive, data_to_respond_with),
            host="localhost",
            port=port,
        )
        servers.append(server)
        return server

    yield create_server

    for server in servers:
        server.close()
        await server.wait_closed()


class TestAsyncMinecraftServer:
    @pytest.mark.asyncio
    async def test_async_ping(self, unused_tcp_port, create_mock_packet_server):
        mock_packet_server = await create_mock_packet_server(
            port=unused_tcp_port,
            data_expected_to_receive=bytearray.fromhex("09010000000001C54246"),
            data_to_respond_with=bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246"),
        )
        minecraft_server = MinecraftServer("localhost", port=unused_tcp_port)

        latency = await minecraft_server.async_ping(ping_token=29704774, version=47)
        assert latency >= 0


class TestMinecraftServer:
    def setup_method(self):
        self.socket = Connection()
        self.server = MinecraftServer("localhost", port=25565)

    def test_ping(self):
        self.socket.receive(bytearray.fromhex("09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            latency = self.server.ping(ping_token=29704774, version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert latency >= 0

    def test_ping_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception):
                    self.server.ping()
                assert pinger.call_count == 3

    def test_status(self):
        self.socket.receive(
            bytearray.fromhex(
                "6D006B7B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F636F6C223A34377D7D09010000000001C54246"
            )
        )

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.status(ping_token=29704774, version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F096C6F63616C686F737463DD01010009010000000001C54246")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert info.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8", "protocol": 47},
        }
        assert info.latency >= 0

    def test_status_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception):
                    self.server.status()
                assert pinger.call_count == 3

    def test_query(self):
        self.socket.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.socket.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"
            )
        )

        self.socket.remaining = Mock()
        self.socket.remaining.side_effect = [15, 208]

        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.query()

        conn_bytes = self.socket.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert info.raw == {
            "hostname": "A Minecraft Server",
            "gametype": "SMP",
            "game_id": "MINECRAFT",
            "version": "1.8",
            "plugins": "",
            "map": "world",
            "numplayers": "3",
            "maxplayers": "20",
            "hostport": "25565",
            "hostip": "192.168.56.1",
        }

    def test_query_retry(self):
        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerQuerier") as querier:
                querier.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception):
                    self.server.query()
                assert querier.call_count == 3

    def test_by_address_no_srv(self):
        with patch("dns.resolver.resolve") as resolve:
            resolve.return_value = []
            self.server = MinecraftServer.lookup("example.org")
            resolve.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        assert self.server.host == "example.org"
        assert self.server.port == 25565

    def test_by_address_invalid_srv(self):
        with patch("dns.resolver.resolve") as resolve:
            resolve.side_effect = [Exception]
            self.server = MinecraftServer.lookup("example.org")
            resolve.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        assert self.server.host == "example.org"
        assert self.server.port == 25565

    def test_by_address_with_srv(self):
        with patch("dns.resolver.resolve") as resolve:
            answer = Mock()
            answer.target = "different.example.org."
            answer.port = 12345
            resolve.return_value = [answer]
            self.server = MinecraftServer.lookup("example.org")
            resolve.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        assert self.server.host == "different.example.org"
        assert self.server.port == 12345

    def test_by_address_with_port(self):
        self.server = MinecraftServer.lookup("example.org:12345")
        assert self.server.host == "example.org"
        assert self.server.port == 12345

    def test_by_address_with_multiple_ports(self):
        with pytest.raises(ValueError):
            MinecraftServer.lookup("example.org:12345:6789")

    def test_by_address_with_invalid_port(self):
        with pytest.raises(ValueError):
            MinecraftServer.lookup("example.org:port")
