import random
from mcstatus.protocol.connection import Connection


class ServerQuerier:
    MAGIC_PREFIX = bytearray.fromhex("FEFD")
    PACKET_TYPE_CHALLENGE = 9
    PACKET_TYPE_QUERY = 0

    def __init__(self, connection):
        self.connection = connection
        self.challenge = 0

    def _create_packet(self, id):
        packet = Connection()
        packet.write(self.MAGIC_PREFIX)
        packet.write(chr(id))
        packet.write_uint(0)
        packet.write_uint(self.challenge)
        return packet

    def _read_packet(self):
        packet = Connection()
        packet.receive(self.connection.read(self.connection.remaining()))
        packet.read(1 + 4)
        return packet

    def handshake(self):
        self.connection.write(self._create_packet(self.PACKET_TYPE_CHALLENGE))

        packet = self._read_packet()
        self.challenge = int(packet.read_ascii())

    def read_query(self):
        request = self._create_packet(self.PACKET_TYPE_QUERY)
        request.write_uint(0)
        self.connection.write(request)

        response = self._read_packet()
        response.read(len("splitnum") + 1 + 1 + 1)
        data = {}
        players = []

        while True:
            key = response.read_ascii()
            if len(key) == 0:
                response.read(1)
                break
            value = response.read_ascii()
            data[key] = value

        response.read(len("player_") + 1 + 1)

        while True:
            name = response.read_ascii()
            if len(name) == 0:
                break
            players.append(name)

        return QueryResponse(data, players)


class QueryResponse:
    def __init__(self, raw, players):
        self.raw = raw
        self.players = players