from unittest import TestCase

from mcstatus.protocol.connection import Connection
from mcstatus.querier import ServerQuerier, QueryResponse


class TestQuerier(TestCase):
    def setUp(self):
        self.querier = ServerQuerier(Connection())

    def test_handshake(self):
        self.querier.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.querier.handshake()

        self.assertEqual(self.querier.connection.flush(), bytearray.fromhex("FEFD090000000000000000"))
        self.assertEqual(self.querier.challenge, 570350778)

    def test_query(self):
        self.querier.connection.receive(bytearray.fromhex("00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"))
        response = self.querier.read_query()

        self.assertEqual(self.querier.connection.flush(), bytearray.fromhex("FEFD00000000000000000000000000"))
        self.assertEqual(response.raw, {
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
        self.assertEqual(response.players.names, ["Dinnerbone", "Djinnibone", "Steve"])


class TestQueryResponse(TestCase):
    def setUp(self):
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

        self.assertEqual(response.motd, "A Minecraft Server")
        self.assertEqual(response.map, "world")
        self.assertEqual(response.players.online, 3)
        self.assertEqual(response.players.max, 20)
        self.assertEqual(response.players.names, ["Dinnerbone", "Djinnibone", "Steve"])
        self.assertEqual(response.software.brand, "vanilla")
        self.assertEqual(response.software.version, "1.8")
        self.assertEqual(response.software.plugins, [])


class TestQueryResponsePlayers(TestCase):
    def test_valid(self):
        players = QueryResponse.Players(5, 20, ["Dinnerbone", "Djinnibone", "Steve"])

        self.assertEqual(players.online, 5)
        self.assertEqual(players.max, 20)
        self.assertEqual(players.names, ["Dinnerbone", "Djinnibone", "Steve"])


class TestQueryResponseSoftware(TestCase):
    def test_vanilla(self):
        software = QueryResponse.Software("1.8", "")

        self.assertEqual(software.brand, "vanilla")
        self.assertEqual(software.version, "1.8")
        self.assertEqual(software.plugins, [])

    def test_modded(self):
        software = QueryResponse.Software("1.8", "A modded server: Foo 1.0; Bar 2.0; Baz 3.0")

        self.assertEqual(software.brand, "A modded server")
        self.assertEqual(software.plugins, ["Foo 1.0", "Bar 2.0", "Baz 3.0"])

    def test_modded_no_plugins(self):
        software = QueryResponse.Software("1.8", "A modded server")

        self.assertEqual(software.brand, "A modded server")
        self.assertEqual(software.plugins, [])