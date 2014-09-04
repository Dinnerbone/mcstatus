import socket
import struct


class Connection:
    def __init__(self):
        self.sent = bytearray()
        self.received = bytearray()

    def read(self, length):
        result = self.received[:length]
        self.received = self.received[length:]
        return result

    def write(self, data):
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

    def read_short(self):
        return self._unpack("h", self.read(2))

    def write_short(self, value):
        self.write(self._pack("h", value))

    def read_ushort(self):
        return self._unpack("H", self.read(2))

    def write_ushort(self, value):
        self.write(self._pack("H", value))

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
    def __init__(self, addr):
        Connection.__init__(self)
        self.socket = socket.create_connection(addr, timeout=10)

    def flush(self):
        raise TypeError("SocketConnection does not support flush()")

    def receive(self, data):
        raise TypeError("SocketConnection does not support receive()")

    def remaining(self):
        raise TypeError("SocketConnection does not support remaining()")

    def read(self, length):
        result = bytearray()
        while len(result) < length:
            result.extend(self.socket.recv(length - len(result)))
        return result

    def write(self, data):
        self.socket.send(data)