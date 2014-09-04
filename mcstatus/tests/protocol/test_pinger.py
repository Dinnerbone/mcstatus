from unittest import TestCase

from mcstatus.protocol.connection import Connection
from mcstatus.pinger import ServerPinger


class TestServerPinger(TestCase):
    def setUp(self):
        self.pinger = ServerPinger(Connection(), host="localhost", port=25565, version=44)

    def test_handshake(self):
        self.pinger.handshake()

        self.assertEqual(self.pinger.connection.flush(), "\x0F\x00\x2C\x09\x6C\x6F\x63\x61\x6C\x68\x6F\x73\x74\x63\xDD\x01")

    def test_read_status(self):
        self.pinger.connection.receive("\x72\x00\x70\x7B\x22\x64\x65\x73\x63\x72\x69\x70\x74\x69\x6F\x6E\x22\x3A\x22\x41\x20\x4D\x69\x6E\x65\x63\x72\x61\x66\x74\x20\x53\x65\x72\x76\x65\x72\x22\x2C\x22\x70\x6C\x61\x79\x65\x72\x73\x22\x3A\x7B\x22\x6D\x61\x78\x22\x3A\x32\x30\x2C\x22\x6F\x6E\x6C\x69\x6E\x65\x22\x3A\x30\x7D\x2C\x22\x76\x65\x72\x73\x69\x6F\x6E\x22\x3A\x7B\x22\x6E\x61\x6D\x65\x22\x3A\x22\x31\x2E\x38\x2D\x70\x72\x65\x31\x22\x2C\x22\x70\x72\x6F\x74\x6F\x63\x6F\x6C\x22\x3A\x34\x34\x7D\x7D")

        self.assertEqual(self.pinger.read_status(), '{"description":"A Minecraft Server","players":{"max":20,"online":0},"version":{"name":"1.8-pre1","protocol":44}}')
        self.assertEqual(self.pinger.connection.flush(), "\x01\x00")

    def test_read_status_invalid(self):
        self.pinger.connection.receive("\x01\x05")

        self.assertRaises(IOError, self.pinger.read_status)

    def test_test_ping(self):
        self.pinger.connection.receive("\x09\x01\x00\x00\x00\x00\x00\xDD\x7D\x1C")
        self.pinger.ping_token = 14515484

        self.assertTrue(self.pinger.test_ping() >= 0)
        self.assertEqual(self.pinger.connection.flush(), "\x09\x01\x00\x00\x00\x00\x00\xDD\x7D\x1C")

    def test_test_ping_invalid(self):
        self.pinger.connection.receive("\x01\x1F")
        self.pinger.ping_token = 14515484

        self.assertRaises(IOError, self.pinger.test_ping)

    def test_test_ping_wrong_token(self):
        self.pinger.connection.receive("\x09\x01\x00\x00\x00\x00\x00\xDD\x7D\x1C")
        self.pinger.ping_token = 12345

        self.assertRaises(IOError, self.pinger.test_ping)