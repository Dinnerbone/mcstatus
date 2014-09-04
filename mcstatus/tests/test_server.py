from unittest import TestCase

from mock import patch

from mcstatus.protocol.connection import Connection
from mcstatus.server import MinecraftServer


class TestMinecraftServer(TestCase):
    def setUp(self):
        self.socket = Connection()
        self.server = MinecraftServer("localhost", port=25565)

    def test_ping_server(self):
        self.socket.receive(bytearray.fromhex("6D006B7B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F636F6C223A34377D7D09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.ping_server(ping_token=29704774, version=47)

        self.assertEqual(self.socket.flush(), bytearray.fromhex("0F002F096C6F63616C686F737463DD01010009010000000001C54246"))
        self.assertEqual(self.socket.remaining(), 0, msg="Data is pending to be read, but should be empty")
        self.assertEqual(info["status"], {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8","protocol":47}})
        self.assertTrue(info["latency"] >= 0)

    def test_ping_server_invalid_json(self):
        self.socket.receive(bytearray.fromhex("6D006B7C226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F636F6C223A34377D7D09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            self.assertRaises(IOError, self.server.ping_server, ping_token=29704774, version=47)