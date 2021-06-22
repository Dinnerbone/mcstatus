import asyncio
from asyncio import StreamReader

import pytest
from mock import patch

from mcstatus.protocol.connection import TCPAsyncSocketConnection


class FakeAsyncStream(StreamReader):
    async def read(self, n: int = ...) -> bytes:
        await asyncio.sleep(delay=10**3)
        return bytes([0] * n)


def fake_asyncio_asyncio_open_connection(hostname, port):
    return FakeAsyncStream(), None


class TestAsyncSocketConnection:
    def setup_method(self):
        self.tcp_async_socket = TCPAsyncSocketConnection()

    def test_tcp_socket_read(self):
        with patch("asyncio.open_connection") as open_conn:
            open_conn.return_value = (FakeAsyncStream(), None)
            asyncio.run(self.tcp_async_socket.connect('dummy_address', timeout=1))

            with pytest.raises(asyncio.exceptions.TimeoutError):
                asyncio.run(self.tcp_async_socket.read(10))
