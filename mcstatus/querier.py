import random
import struct
from typing import List

from mcstatus.protocol.connection import Connection


class ServerQuerier:
    MAGIC_PREFIX = bytearray.fromhex("FEFD")
    PADDING = bytearray.fromhex("00000000")
    PACKET_TYPE_CHALLENGE = 9
    PACKET_TYPE_QUERY = 0

    def __init__(self, connection):
        self.connection = connection
        self.challenge = 0

    @staticmethod
    def _generate_session_id():
        # minecraft only supports lower 4 bits
        return random.randint(0, 2 ** 31) & 0x0F0F0F0F

    def _create_packet(self):
        packet = Connection()
        packet.write(self.MAGIC_PREFIX)
        packet.write(struct.pack("!B", self.PACKET_TYPE_QUERY))
        packet.write_uint(self._generate_session_id())
        packet.write_int(self.challenge)
        packet.write(self.PADDING)
        return packet

    def _create_handshake_packet(self):
        packet = Connection()
        packet.write(self.MAGIC_PREFIX)
        packet.write(struct.pack("!B", self.PACKET_TYPE_CHALLENGE))
        packet.write_uint(self._generate_session_id())
        return packet

    def _read_packet(self):
        packet = Connection()
        packet.receive(self.connection.read(self.connection.remaining()))
        packet.read(1 + 4)
        return packet

    def handshake(self):
        self.connection.write(self._create_handshake_packet())

        packet = self._read_packet()
        self.challenge = int(packet.read_ascii())

    def read_query(self):
        request = self._create_packet()
        self.connection.write(request)

        response = self._read_packet()
        return QueryResponse.from_connection(response)


class AsyncServerQuerier(ServerQuerier):
    async def _read_packet(self):
        packet = Connection()
        packet.receive(await self.connection.read(self.connection.remaining()))
        packet.read(1 + 4)
        return packet

    async def handshake(self):
        await self.connection.write(self._create_handshake_packet())

        packet = await self._read_packet()
        self.challenge = int(packet.read_ascii())

    async def read_query(self):
        request = self._create_packet()
        await self.connection.write(request)

        response = await self._read_packet()
        return QueryResponse.from_connection(response)


class QueryResponse:
    # THIS IS SO UNPYTHONIC
    # it's staying just because the tests depend on this structure
    class Players:
        online: int
        max: int
        names: List[str]

        def __init__(self, online, max, names):
            self.online = int(online)
            self.max = int(max)
            self.names = names

    class Software:
        version: str
        brand: str
        plugins: List[str]

        def __init__(self, version, plugins):
            self.version = version
            self.brand = "vanilla"
            self.plugins = []

            if plugins:
                parts = plugins.split(":", 1)
                self.brand = parts[0].strip()

                if len(parts) == 2:
                    self.plugins = [s.strip() for s in parts[1].split(";")]

    motd: str
    map: str
    players: Players
    software: Software

    def __init__(self, raw, players):
        try:
            self.raw = raw
            self.motd = raw["hostname"]
            self.map = raw["map"]
            self.players = QueryResponse.Players(raw["numplayers"], raw["maxplayers"], players)
            self.software = QueryResponse.Software(raw["version"], raw["plugins"])
        except:
            raise ValueError("The provided data is not valid")

    @classmethod
    def from_connection(cls, response: Connection):
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

        return cls(data, players)
