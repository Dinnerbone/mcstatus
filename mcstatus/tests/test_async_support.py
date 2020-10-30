from unittest import TestCase

from inspect import iscoroutinefunction

from mcstatus.protocol.connection import TCPAsyncSocketConnection

class TCPAsyncSocketConnectionTests(TestCase):
    def test_is_completely_asynchronous(self):
        conn = TCPAsyncSocketConnection()

        for attribute in dir(conn):
            if attribute.startswith("read_"):
                self.assertTrue(iscoroutinefunction(conn.__getattribute__(attribute)))