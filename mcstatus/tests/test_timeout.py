from mock import patch
import sys

import asyncio
import pytest

from mcstatus.protocol.connection import TCPAsyncSocketConnection


class FakeAsyncStream(asyncio.StreamReader):
    async def read(self, n: int) -> bytes:
        await asyncio.sleep(delay=2)
        return bytes([0] * n)


def fake_asyncio_asyncio_open_connection(hostname, port):
    return FakeAsyncStream(), None


@pytest.mark.skipif(sys.platform.startswith("win"), reason="async bug on Windows https://github.com/Dinnerbone/mcstatus/issues/140")
class TestAsyncSocketConnection:
    def setup_method(self):
        self.tcp_async_socket = TCPAsyncSocketConnection()

    def test_tcp_socket_read(self):
        try:
            from asyncio.exceptions import TimeoutError
        except ImportError:
            from asyncio import TimeoutError

        loop = asyncio.get_event_loop()
        with patch("asyncio.open_connection") as open_conn:
            open_conn.return_value = (FakeAsyncStream(), None)
            loop.run_until_complete(self.tcp_async_socket.connect("dummy_address", timeout=0.01))

            with pytest.raises(TimeoutError):
                loop.run_until_complete(self.tcp_async_socket.read(10))
