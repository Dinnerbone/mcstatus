from unittest.mock import Mock

from mcstatus.protocol.connection import Connection
from mcstatus.querier import ServerQuerier


class TestHandshake:
    def setup_method(self):
        self.querier = ServerQuerier(Connection())  # type: ignore[arg-type]

    def test_session_id(self):
        def session_id():
            return 0x01010101

        self.querier.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.querier._generate_session_id = Mock()
        self.querier._generate_session_id = session_id
        self.querier.handshake()

        conn_bytes = self.querier.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert conn_bytes[3:] == session_id().to_bytes(4, byteorder="big")
        assert self.querier.challenge == 570350778
