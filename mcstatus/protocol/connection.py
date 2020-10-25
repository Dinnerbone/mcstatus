import socket
import struct
import asyncio

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
            data = bytearray(data.flush())
        if isinstance(data, str):
            data = bytearray(data)
        self.sent.extend(data)

    def receive(self, data):
        if not isinstance(data, bytearray):
            data = bytearray(data)
        self.received.extend(data)

    def remaining(self):
        return len(self.received)

    def flush(self):
        result = self.sent
        self.sent = ""
        return result

    def _unpack(self, format, data):
        return struct.unpack(">" + format, bytes(data))[0]

    def _pack(self, format, data):
        return struct.pack(">" + format, data)

    def read_varint(self):
        result = 0
        for i in range(5):
            part = ord(self.read(1))
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return result
        raise IOError("Server sent a varint that was too big!")

    def write_varint(self, value):
        remaining = value
        for i in range(5):
            if remaining & ~0x7F == 0:
                self.write(struct.pack("!B", remaining))
                return
            self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError("The value %d is too big to send in a varint" % value)

    def read_utf(self):
        length = self.read_varint()
        return self.read(length).decode('utf8')

    def write_utf(self, value):
        self.write_varint(len(value))
        self.write(bytearray(value, 'utf8'))

    def read_ascii(self):
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(self.read(1))
        return result[:-1].decode("ISO-8859-1")

    def write_ascii(self, value):
        self.write(bytearray(value, 'ISO-8859-1'))
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
        self.socket = socket.socket(socket.AF_INET if ip_type(addr[0]) == 4 else socket.AF_INET6, socket.SOCK_DGRAM)
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

class TCPAsyncSocketConnection(TCPSocketConnection):
    def __init__(self):
        pass

    async def connect(self, addr, timeout=3):
        conn = asyncio.open_connection(addr[0], addr[1])
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=timeout)

    async def read(self, length):
        result = bytearray()
        while len(result) < length:
            new = await self.reader.read(length - len(result))
            if len(new) == 0:
                raise IOError("Server did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data):
        self.writer.write(data)
    
    async def read_varint(self):
        result = 0
        for i in range(5):
            part = ord(await self.read(1))
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return result
        raise IOError("Server sent a varint that was too big!")

    async def read_utf(self):
        length = await self.read_varint()
        return self.read(length).decode('utf8')

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