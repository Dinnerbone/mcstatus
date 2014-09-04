import datetime
import random

from mcstatus.protocol.connection import Connection


class ServerPinger:
    def __init__(self, connection, host="", port=0, version=47, ping_token=None):
        if ping_token is None:
            ping_token = random.randint(0, 1 << 63 - 1)
        self.version = version
        self.connection = connection
        self.host = host
        self.port = port
        self.ping_token = ping_token

    def handshake(self):
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.host)
        packet.write_short(self.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    def read_status(self):
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        if response.read_varint() != 0:
            raise IOError("Received invalid query response packet.")
        return response.read_utf()

    def test_ping(self):
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        received = datetime.datetime.now()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError("Received mangled ping response packet (expected token %d, received %d)" % (self.ping_token, received_token))

        delta = (received - sent)
        # We have no trivial way of getting a time delta :(
        return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000.0