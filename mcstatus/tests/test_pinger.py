from unittest import TestCase

from mcstatus.protocol.connection import Connection
from mcstatus.pinger import ServerPinger, PingResponse
from mcstatus.server import MinecraftServer


class TestServerPinger(TestCase):
    def setUp(self):
        self.pinger = ServerPinger(Connection(), host="localhost", port=25565, version=44)

    def test_handshake(self):
        self.pinger.handshake()

        self.assertEqual(self.pinger.connection.flush(), bytearray.fromhex("0F002C096C6F63616C686F737463DD01"))

    def test_read_status(self):
        self.pinger.connection.receive(bytearray.fromhex("7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"))
        status = self.pinger.read_status()

        self.assertEqual(status.raw, {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})
        self.assertEqual(self.pinger.connection.flush(), bytearray.fromhex("0100"))

    def test_read_status_invalid_json(self):
        self.pinger.connection.receive(bytearray.fromhex("0300017B"))
        self.assertRaises(IOError, self.pinger.read_status)

    def test_read_status_invalid_reply(self):
        self.pinger.connection.receive(bytearray.fromhex("4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"))

        self.assertRaises(IOError, self.pinger.read_status)

    def test_read_status_invalid_status(self):
        self.pinger.connection.receive(bytearray.fromhex("0105"))

        self.assertRaises(IOError, self.pinger.read_status)

    def test_test_ping(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 14515484

        self.assertTrue(self.pinger.test_ping() >= 0)
        self.assertEqual(self.pinger.connection.flush(), bytearray.fromhex("09010000000000DD7D1C"))

    def test_test_ping_invalid(self):
        self.pinger.connection.receive(bytearray.fromhex("011F"))
        self.pinger.ping_token = 14515484

        self.assertRaises(IOError, self.pinger.test_ping)

    def test_test_ping_wrong_token(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 12345

        self.assertRaises(IOError, self.pinger.test_ping)


class TestPingResponse(TestCase):
    def test_raw(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

        self.assertEqual(response.raw, {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

    def test_description(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

        self.assertEqual(response.description, "A Minecraft Server")

    def test_description_missing(self):
        self.assertRaises(ValueError, PingResponse, {"players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

    def test_version(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

        self.assertIsNotNone(response.version)
        self.assertEqual(response.version.name, "1.8-pre1")
        self.assertEqual(response.version.protocol, 44)

    def test_version_missing(self):
        self.assertRaises(ValueError, PingResponse, {"description":"A Minecraft Server","players":{"max":20,"online":0}})

    def test_version_invalid(self):
        self.assertRaises(ValueError, PingResponse, {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":"foo"})

    def test_players(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":5},"version":{"name":"1.8-pre1","protocol":44}})

        self.assertIsNotNone(response.players)
        self.assertEqual(response.players.max, 20)
        self.assertEqual(response.players.online, 5)

    def test_players_missing(self):
        self.assertRaises(ValueError, PingResponse, {"description":"A Minecraft Server","version":{"name":"1.8-pre1","protocol":44}})

    def test_favicon(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44},"favicon":"data:image/png;base64,foo"})

        self.assertEqual(response.favicon, "data:image/png;base64,foo")

    def test_favicon_missing(self):
        response = PingResponse({"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}})

        self.assertIsNone(response.favicon)

class TestPingResponsePlayers(TestCase):
    def test_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players, "foo")

    def test_max_missing(self):
        self.assertRaises(ValueError, PingResponse.Players, {"online":5})

    def test_max_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players, {"max":"foo","online":5})

    def test_online_missing(self):
        self.assertRaises(ValueError, PingResponse.Players, {"max":20})

    def test_online_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players, {"max":20,"online":"foo"})

    def test_valid(self):
        players = PingResponse.Players({"max":20,"online":5})

        self.assertEqual(players.max, 20)
        self.assertEqual(players.online, 5)

    def test_sample(self):
        players = PingResponse.Players({"max":20,"online":1,"sample":[{"name":'Dinnerbone','id':"61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"}]})

        self.assertIsNotNone(players.sample)
        self.assertEqual(players.sample[0].name, "Dinnerbone")

    def test_sample_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players, {"max":20,"online":1,"sample":"foo"})

    def test_sample_missing(self):
        players = PingResponse.Players({"max":20,"online":1})
        self.assertIsNone(players.sample)


class TestPingResponsePlayersPlayer(TestCase):
    def test_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players.Player, "foo")

    def test_name_missing(self):
        self.assertRaises(ValueError, PingResponse.Players.Player, {"id":"61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

    def test_name_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players.Player, {"name":{},"id":"61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

    def test_id_missing(self):
        self.assertRaises(ValueError, PingResponse.Players.Player, {"name":"Dinnerbone"})

    def test_id_invalid(self):
        self.assertRaises(ValueError, PingResponse.Players.Player, {"name":"Dinnerbone","id":{}})

    def test_valid(self):
        player = PingResponse.Players.Player({"name":'Dinnerbone','id':"61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

        self.assertEqual(player.name, "Dinnerbone")
        self.assertEqual(player.id, "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6")


class TestPingResponseVersion(TestCase):
    def test_invalid(self):
        self.assertRaises(ValueError, PingResponse.Version, "foo")

    def test_protocol_missing(self):
        self.assertRaises(ValueError, PingResponse.Version, {"name":"foo"})

    def test_protocol_invalid(self):
        self.assertRaises(ValueError, PingResponse.Version, {"name":"foo","protocol":"bar"})

    def test_name_missing(self):
        self.assertRaises(ValueError, PingResponse.Version, {"protocol":5})

    def test_name_invalid(self):
        self.assertRaises(ValueError, PingResponse.Version, {"name":{},"protocol":5})

    def test_valid(self):
        players = PingResponse.Version({"name":"foo","protocol":5})

        self.assertEqual(players.name, "foo")
        self.assertEqual(players.protocol, 5)