from mcstatus.protocol.connection import Connection
from mcstatus.querier import ServerQuerier, QueryResponse


class TestMinecraftQuerier:
    def setup_method(self):
        self.querier = ServerQuerier(Connection())

    def test_handshake(self):
        self.querier.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.querier.handshake()

        conn_bytes = self.querier.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert self.querier.challenge == 570350778

    def test_query(self):
        self.querier.connection.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"
            )
        )
        response = self.querier.read_query()
        conn_bytes = self.querier.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD00")
        assert conn_bytes[7:] == bytearray.fromhex("0000000000000000")
        assert response.raw == {
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
        assert response.players.names == ["Dinnerbone", "Djinnibone", "Steve"]


class TestQueryResponse:
    def setup_method(self):
        self.raw = {
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
        self.players = ["Dinnerbone", "Djinnibone", "Steve"]

    def test_valid(self):
        response = QueryResponse(self.raw, self.players)
        assert response.motd == "A Minecraft Server"
        assert response.map == "world"
        assert response.players.online == 3
        assert response.players.max == 20
        assert response.players.names == ["Dinnerbone", "Djinnibone", "Steve"]
        assert response.software.brand == "vanilla"
        assert response.software.version == "1.8"
        assert response.software.plugins == []

    def test_valid2(self):
        players = QueryResponse.Players(5, 20, ["Dinnerbone", "Djinnibone", "Steve"])
        assert players.online == 5
        assert players.max == 20
        assert players.names == ["Dinnerbone", "Djinnibone", "Steve"]

    def test_vanilla(self):
        software = QueryResponse.Software("1.8", "")
        assert software.brand == "vanilla"
        assert software.version == "1.8"
        assert software.plugins == []

    def test_modded(self):
        software = QueryResponse.Software("1.8", "A modded server: Foo 1.0; Bar 2.0; Baz 3.0")
        assert software.brand == "A modded server"
        assert software.plugins == ["Foo 1.0", "Bar 2.0", "Baz 3.0"]

    def test_modded_no_plugins(self):
        software = QueryResponse.Software("1.8", "A modded server")
        assert software.brand == "A modded server"
        assert software.plugins == []
