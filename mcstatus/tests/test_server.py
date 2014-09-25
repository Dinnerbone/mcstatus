from unittest import TestCase

from mock import patch, Mock

from mcstatus.protocol.connection import Connection
from mcstatus.server import MinecraftServer


class TestMinecraftServer(TestCase):
    def setUp(self):
        self.socket = Connection()
        self.server = MinecraftServer("localhost", port=25565)

    def test_ping(self):
        self.socket.receive(bytearray.fromhex("09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            latency = self.server.ping(ping_token=29704774, version=47)

        self.assertEqual(self.socket.flush(), bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246"))
        self.assertEqual(self.socket.remaining(), 0, msg="Data is pending to be read, but should be empty")
        self.assertTrue(latency >= 0)

    def test_ping_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                self.assertRaises(Exception, self.server.ping)
                self.assertEqual(pinger.call_count, 3)

    def test_status(self):
        self.socket.receive(bytearray.fromhex("6D006B7B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F636F6C223A34377D7D09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.status(ping_token=29704774, version=47)

        self.assertEqual(self.socket.flush(), bytearray.fromhex("0F002F096C6F63616C686F737463DD01010009010000000001C54246"))
        self.assertEqual(self.socket.remaining(), 0, msg="Data is pending to be read, but should be empty")
        self.assertEqual(info.raw, {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8","protocol":47}})
        self.assertTrue(info.latency >= 0)

    def test_status_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                self.assertRaises(Exception, self.server.status)
                self.assertEqual(pinger.call_count, 3)

    def test_query(self):
        self.socket.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.socket.receive(bytearray.fromhex("00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"))

        self.socket.remaining = Mock()
        self.socket.remaining.side_effect = [15, 208]

        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.query()

        self.assertEqual(self.socket.flush(), bytearray.fromhex("FEFD090000000000000000FEFD000000000021FEDCBA00000000"))
        self.assertEqual(info.raw, {
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
        })

    def test_query_retry(self):
        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerQuerier") as querier:
                querier.side_effect = [Exception, Exception, Exception]
                self.assertRaises(Exception, self.server.query)
                self.assertEqual(querier.call_count, 3)

    def test_by_address_no_srv(self):
        with patch("dns.resolver.query") as query:
            query.return_value = []
            self.server = MinecraftServer.lookup("example.org")
            query.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        self.assertEqual(self.server.host, "example.org")
        self.assertEqual(self.server.port, 25565)

    def test_by_address_invalid_srv(self):
        with patch("dns.resolver.query") as query:
            query.side_effect = [Exception]
            self.server = MinecraftServer.lookup("example.org")
            query.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        self.assertEqual(self.server.host, "example.org")
        self.assertEqual(self.server.port, 25565)

    def test_by_address_with_srv(self):
        with patch("dns.resolver.query") as query:
            answer = Mock()
            answer.target = "different.example.org."
            answer.port = 12345
            query.return_value = [answer]
            self.server = MinecraftServer.lookup("example.org")
            query.assert_called_once_with("_minecraft._tcp.example.org", "SRV")
        self.assertEqual(self.server.host, "different.example.org")
        self.assertEqual(self.server.port, 12345)

    def test_by_address_with_port(self):
        self.server = MinecraftServer.lookup("example.org:12345")
        self.assertEqual(self.server.host, "example.org")
        self.assertEqual(self.server.port, 12345)

    def test_by_address_with_multiple_ports(self):
        self.assertRaises(ValueError, MinecraftServer.lookup, "example.org:12345:6789")

    def test_by_address_with_invalid_port(self):
        self.assertRaises(ValueError, MinecraftServer.lookup, "example.org:port")