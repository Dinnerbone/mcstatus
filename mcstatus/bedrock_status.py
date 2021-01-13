from time import perf_counter
import asyncio_dgram
import struct


class BedrockServerStatus:
    def __init__(self, host, port=19132):
        self.host = host
        self.port = port

    async def read_status_async(self):
        start = perf_counter()

        try:
            stream = await asyncio_dgram.connect((self.host, self.port))

            await stream.send(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx')
            data, _ = await stream.recv()
        finally:
            try:
                stream.close()
            except BaseException:
                pass

        latency = perf_counter() - start

        data = data[1:]
        name_length = struct.unpack('>H', data[32:34])[0]
        data = data[34:34+name_length].decode().split(';')

        try:
            map_ = data[7]
            gamemode = data[8]
        except BaseException:
            map_ = None
            gamemode = None

        return BedrockStatusResponse(
            data[2],
            data[0],
            latency,
            data[4],
            data[5],
            data[1],
            map_,
            gamemode
        )


class BedrockStatusResponse:
    class Version:
        def __init__(protocol, brand):
            self.protocol = protocol
            self.brand = brand

    def __init__(protocol, brand, latency, players_online, players_max, motd, map_, gamemode):
        self.version = Version(protocol, brand)
        self.latency = latency
        self.players_online = players_online
        self.players_max = players_max
        self.motd = motd
        self.map = map_
        self.gamemode = gamemode
