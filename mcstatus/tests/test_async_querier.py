from mcstatus.protocol.connection import Connection
from mcstatus.querier import QueryResponse, AsyncServerQuerier
from mcstatus.tests.test_async_pinger import async_decorator  # type: ignore - tests doesn't have __init__.py


class FakeUDPAsyncConnection(Connection):
    async def read(self, length):
        return super().read(length)

    async def write(self, data):
        return super().write(data)


class TestMinecraftAsyncQuerier:
    def setup_method(self):
        self.querier = AsyncServerQuerier(FakeUDPAsyncConnection())

    def test_handshake(self):
        self.querier.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        async_decorator(self.querier.handshake)()
        assert self.querier.connection.flush() == bytearray.fromhex("FEFD090000000000000000")
        assert self.querier.challenge == 570350778

    def test_query(self):
        self.querier.connection.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d657479706500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d617000776f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053746576650000"
            )
        )
        response = async_decorator(self.querier.read_query)()
        assert self.querier.connection.flush() == bytearray.fromhex("FEFD00000000000000000000000000")
        assert response.raw == {
            "hostname": "A Minecraft Server",
            "gametype": "SMP",
            "game_id": "MINECRAFT",
            "version": "1.8",
            "plugins": "",
            "map": "world",
            "numplayers": "3",
            "maxplayers": "20",
            "hostport": "25565",
            "hostip": "192.168.56.1",
        }
        assert response.players.names == ["Dinnerbone", "Djinnibone", "Steve"]
