from unittest import TestCase

from mcstatus.protocol.connection import Connection
from mcstatus.pinger import ServerPinger


class TestServerPinger(TestCase):
    def setUp(self):
        self.pinger = ServerPinger(Connection(), host="localhost", port=25565, version=44)

    def test_handshake(self):
        self.pinger.handshake()

        self.assertEqual(self.pinger.connection.flush(), bytearray.fromhex("0F002C096C6F63616C686F737463DD01"))

    def test_read_status(self):
        self.pinger.connection.receive(bytearray.fromhex("7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"))

        self.assertEqual(self.pinger.read_status(), '{"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}}')
        self.assertEqual(self.pinger.connection.flush(), bytearray.fromhex("0100"))

    def test_read_status_invalid(self):
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