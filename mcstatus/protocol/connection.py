from abc import abstractmethod, ABC
import socket
import struct
import asyncio
import asyncio_dgram

from ctypes import c_uint32 as unsigned_int32
from ctypes import c_int32 as signed_int32

from ..scripts.address_tools import ip_type


class Connection:
    def __init__(self):
        self.sent = bytearray()
        self.received = bytearray()

    def read(self, length):
        result = self.received[:length]
        self.received = self.received[length:]
        return result

    def write(self, data):
        if isinstance(data, Connection):
            data = data.flush()
        if isinstance(data, str):
            data = bytearray(data, "utf-8")
        self.sent.extend(data)

    def receive(self, data):
        if not isinstance(data, bytearray):
            data = bytearray(data)
        self.received.extend(data)

    def remaining(self):
        return len(self.received)

    def flush(self):
        result = self.sent
        self.sent = bytearray()
        return result

    def _unpack(self, format, data):
        return struct.unpack(">" + format, bytes(data))[0]

    def _pack(self, format, data):
        return struct.pack(">" + format, data)

    def read_varint(self):
        result = 0
        for i in range(5):
            part = self.read(1)[0]
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError("Server sent a varint that was too big!")

    def write_varint(self, value):
        if value < -(2 ** 31) or 2 ** 31 - 1 < value:
            raise ValueError("Minecraft varints must be in the range of [-2**31, 2**31 - 1].")
        remaining = unsigned_int32(value).value
        for i in range(5):
            if remaining & ~0x7F == 0:
                self.write(struct.pack("!B", remaining))
                return
            self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7

    def read_utf(self):
        length = self.read_varint()
        return self.read(length).decode("utf8")

    def write_utf(self, value):
        self.write_varint(len(value))
        self.write(bytearray(value, "utf8"))

    def read_ascii(self):
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(self.read(1))
        return result[:-1].decode("ISO-8859-1")

    def write_ascii(self, value):
        self.write(bytearray(value, "ISO-8859-1"))
        self.write(bytearray.fromhex("00"))

    def read_short(self):
        return self._unpack("h", self.read(2))

    def write_short(self, value):
        self.write(self._pack("h", value))

    def read_ushort(self):
        return self._unpack("H", self.read(2))

    def write_ushort(self, value):
        self.write(self._pack("H", value))

    def read_int(self):
        return self._unpack("i", self.read(4))

    def write_int(self, value):
        self.write(self._pack("i", value))

    def read_uint(self):
        return self._unpack("I", self.read(4))

    def write_uint(self, value):
        self.write(self._pack("I", value))

    def read_long(self):
        return self._unpack("q", self.read(8))

    def write_long(self, value):
        self.write(self._pack("q", value))

    def read_ulong(self):
        return self._unpack("Q", self.read(8))

    def write_ulong(self, value):
        self.write(self._pack("Q", value))

    def read_buffer(self):
        length = self.read_varint()
        result = Connection()
        result.receive(self.read(length))
        return result

    def write_buffer(self, buffer):
        data = buffer.flush()
        self.write_varint(len(data))
        self.write(data)


class AsyncReadConnection(Connection, ABC):
    @abstractmethod
    async def read(self, length: int) -> bytearray:
        ...

    async def read_varint(self):
        result = 0
        for i in range(5):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError("Server sent a varint that was too big!")

    async def read_utf(self):
        length = await self.read_varint()
        return (await self.read(length)).decode("utf8")

    async def read_ascii(self):
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(await self.read(1))
        return result[:-1].decode("ISO-8859-1")

    async def read_short(self):
        return self._unpack("h", await self.read(2))

    async def read_ushort(self):
        return self._unpack("H", await self.read(2))

    async def read_int(self):
        return self._unpack("i", await self.read(4))

    async def read_uint(self):
        return self._unpack("I", await self.read(4))

    async def read_long(self):
        return self._unpack("q", await self.read(8))

    async def read_ulong(self):
        return self._unpack("Q", await self.read(8))

    async def read_buffer(self):
        length = await self.read_varint()
        result = Connection()
        result.receive(await self.read(length))
        return result


class TCPSocketConnection(Connection):
    def __init__(self, addr, timeout=3):
        Connection.__init__(self)
        self.socket = socket.create_connection(addr, timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def flush(self):
        raise TypeError("TCPSocketConnection does not support flush()")

    def receive(self, data):
        raise TypeError("TCPSocketConnection does not support receive()")

    def remaining(self):
        raise TypeError("TCPSocketConnection does not support remaining()")

    def read(self, length):
        result = bytearray()
        while len(result) < length:
            new = self.socket.recv(length - len(result))
            if len(new) == 0:
                raise IOError("Server did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data):
        self.socket.send(data)

    def __del__(self):
        try:
            self.socket.close()
        except:
            pass


class UDPSocketConnection(Connection):
    def __init__(self, addr, timeout=3):
        Connection.__init__(self)
        self.addr = addr
        self.socket = socket.socket(
            socket.AF_INET if ip_type(addr[0]) == 4 else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        self.socket.settimeout(timeout)

    def flush(self):
        raise TypeError("UDPSocketConnection does not support flush()")

    def receive(self, data):
        raise TypeError("UDPSocketConnection does not support receive()")

    def remaining(self):
        return 65535

    def read(self, length):
        result = bytearray()
        while len(result) == 0:
            result.extend(self.socket.recvfrom(self.remaining())[0])
        return result

    def write(self, data):
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        self.socket.sendto(data, self.addr)

    def __del__(self):
        try:
            self.socket.close()
        except:
            pass


class TCPAsyncSocketConnection(AsyncReadConnection):
    reader = None
    writer = None
    timeout = None

    def __init__(self):
        super().__init__()

    async def connect(self, addr, timeout=3):
        self.timeout = timeout
        conn = asyncio.open_connection(addr[0], addr[1])
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=self.timeout)

    async def read(self, length):
        result = bytearray()
        while len(result) < length:
            new = await asyncio.wait_for(self.reader.read(length - len(result)), timeout=self.timeout)
            if len(new) == 0:
                raise IOError("Server did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data):
        self.writer.write(data)

    def close(self):
        self.writer.close()


class UDPAsyncSocketConnection(AsyncReadConnection):
    stream = None
    timeout = None

    def __init__(self):
        super().__init__()

    async def connect(self, addr, timeout=3):
        self.timeout = timeout
        conn = asyncio_dgram.connect((addr[0], addr[1]))
        self.stream = await asyncio.wait_for(conn, timeout=self.timeout)

    def flush(self):
        raise TypeError("UDPSocketConnection does not support flush()")

    def receive(self, data):
        raise TypeError("UDPSocketConnection does not support receive()")

    def remaining(self):
        return 65535

    async def read(self, length):
        data, remote_addr = await asyncio.wait_for(self.stream.recv(), timeout=self.timeout)
        return data

    async def write(self, data):
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        await self.stream.send(data)

    def __del__(self):
        try:
            self.stream.close()
        except:
            pass
