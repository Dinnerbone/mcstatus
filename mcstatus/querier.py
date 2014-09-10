import struct

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
        packet.write(struct.pack("!B", id))
        packet.write_uint(0)
        packet.write_int(self.challenge)
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
    class Players:
        def __init__(self, online, max, names):
            self.online = int(online)
            self.max = int(max)
            self.names = names

    class Software:
        def __init__(self, version, plugins):
            self.version = version
            self.brand = "vanilla"
            self.plugins = []

            if plugins:
                parts = plugins.split(":", 1)
                self.brand = parts[0].strip()

                if len(parts) == 2:
                    self.plugins = [s.strip() for s in parts[1].split(";")]


    def __init__(self, raw, players):
        self.raw = raw
        self.motd = raw["hostname"]
        self.map = raw["map"]
        self.players = QueryResponse.Players(raw["numplayers"], raw["maxplayers"], players)
        self.software = QueryResponse.Software(raw["version"], raw["plugins"])