from unittest import TestCase

from mock import patch, Mock

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
            info, latency = self.server.ping_server(ping_token=29704774, version=47)

        self.assertEqual(self.socket.flush(), bytearray.fromhex("0F002F096C6F63616C686F737463DD01010009010000000001C54246"))
        self.assertEqual(self.socket.remaining(), 0, msg="Data is pending to be read, but should be empty")
        self.assertEqual(info.raw, {"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8","protocol":47}})
        self.assertTrue(latency >= 0)

    def test_query_server(self):
        self.socket.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.socket.receive(bytearray.fromhex("00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"))

        self.socket.remaining = Mock()
        self.socket.remaining.side_effect = [15, 208]

        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.query_server()

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