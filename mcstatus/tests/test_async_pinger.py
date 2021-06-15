import asyncio
import pytest

from mcstatus.protocol.connection import Connection
from mcstatus.pinger import AsyncServerPinger, PingResponse
from mcstatus.server import MinecraftServer


def async_decorator(f):
    async def cor(*args, **kwargs):
        return await f(*args, **kwargs)

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(cor(*args, **kwargs))

    return wrapper


class FakeAsyncConnection(Connection):
    async def read_buffer(self):
        return super().read_buffer()


class TestAsyncServerPinger:
    def setup_method(self):
        self.pinger = AsyncServerPinger(FakeAsyncConnection(), host="localhost", port=25565, version=44)

    def test_handshake(self):
        self.pinger.handshake()

        assert self.pinger.connection.flush() == bytearray.fromhex("0F002C096C6F63616C686F737463DD01")

    def test_read_status(self):
        self.pinger.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )
        status = async_decorator(self.pinger.read_status)()

        assert status.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
        }
        assert self.pinger.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.pinger.connection.receive(bytearray.fromhex("0300017B"))
        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_read_status_invalid_reply(self):
        self.pinger.connection.receive(
            bytearray.fromhex(
                "4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_read_status_invalid_status(self):
        self.pinger.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_test_ping(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 14515484

        assert async_decorator(self.pinger.test_ping)() >= 0
        assert self.pinger.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self):
        self.pinger.connection.receive(bytearray.fromhex("011F"))
        self.pinger.ping_token = 14515484

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_test_ping_wrong_token(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 12345

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()
