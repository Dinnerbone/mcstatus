import asyncio
import socket
import struct
from time import perf_counter
from typing import Optional

import asyncio_dgram


class BedrockServerStatus:
    request_status_data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx"

    def __init__(self, host, port=19132, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout

    @staticmethod
    def parse_response(data: bytes, latency: float):
        data = data[1:]
        name_length = struct.unpack(">H", data[32:34])[0]
        decoded_data = data[34 : 34 + name_length].decode().split(";")

        map_: Optional[str]
        gamemode: Optional[str]
        try:
            map_ = decoded_data[7]
            gamemode = decoded_data[8]
        except BaseException:
            map_ = None
            gamemode = None

        return BedrockStatusResponse(
            protocol=decoded_data[2],
            brand=decoded_data[0],
            version=decoded_data[3],
            latency=latency,
            players_online=decoded_data[4],
            players_max=decoded_data[5],
            motd=decoded_data[1],
            map_=map_,
            gamemode=gamemode,
        )

    def read_status(self):
        start = perf_counter()

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        s.sendto(self.request_status_data, (self.host, self.port))
        data, _ = s.recvfrom(2048)

        return self.parse_response(data, (perf_counter() - start))

    async def read_status_async(self):
        start = perf_counter()

        try:
            conn = asyncio_dgram.connect((self.host, self.port))
            stream = await asyncio.wait_for(conn, timeout=self.timeout)

            await asyncio.wait_for(stream.send(self.request_status_data), timeout=self.timeout)
            data, _ = await asyncio.wait_for(stream.recv(), timeout=self.timeout)
        finally:
            try:
                stream.close()
            except BaseException:
                pass

        return self.parse_response(data, (perf_counter() - start))


class BedrockStatusResponse:
    class Version:
        def __init__(self, protocol, brand, version):
            self.protocol = protocol
            self.brand = brand
            self.version = version

    def __init__(
        self,
        protocol,
        brand,
        version,
        latency,
        players_online,
        players_max,
        motd,
        map_,
        gamemode,
    ):
        self.version = self.Version(protocol, brand, version)
        self.latency = latency
        self.players_online = players_online
        self.players_max = players_max
        self.motd = motd
        self.map = map_
        self.gamemode = gamemode
