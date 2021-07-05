import pytest

from mock import Mock, patch

from mcstatus.protocol.connection import (
    Connection,
    TCPSocketConnection,
    UDPSocketConnection,
)


class TestConnection:
    connection: Connection

    def setup_method(self):
        self.connection = Connection()

    def test_flush(self):
        self.connection.sent = bytearray.fromhex("7FAABB")

        assert self.connection.flush() == bytearray.fromhex("7FAABB")
        assert self.connection.sent == bytearray()

    def test_receive(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        assert self.connection.received == bytearray.fromhex("7FAABB")

    def test_remaining(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        assert self.connection.remaining() == 3

    def test_send(self):
        self.connection.write(bytearray.fromhex("7F"))
        self.connection.write(bytearray.fromhex("AABB"))

        assert self.connection.flush() == bytearray.fromhex("7FAABB")

    def test_read(self):
        self.connection.receive(bytearray.fromhex("7FAABB"))

        assert self.connection.read(2) == bytearray.fromhex("7FAA")
        assert self.connection.read(1) == bytearray.fromhex("BB")

    def _assert_varint_read_write(self, hexstr, value):
        self.connection.receive(bytearray.fromhex(hexstr))
        assert self.connection.read_varint() == value

        self.connection.write_varint(value)
        assert self.connection.flush() == bytearray.fromhex(hexstr)

    def test_varint_cases(self):
        self._assert_varint_read_write("00", 0)
        self._assert_varint_read_write("01", 1)
        self._assert_varint_read_write("0F", 15)
        self._assert_varint_read_write("FFFFFFFF07", 2147483647)

        self._assert_varint_read_write("FFFFFFFF0F", -1)
        self._assert_varint_read_write("8080808008", -2147483648)

    def test_readInvalidVarInt(self):
        self.connection.receive(bytearray.fromhex("FFFFFFFF80"))

        with pytest.raises(IOError):
            self.connection.read_varint()

    def test_writeInvalidVarInt(self):
        with pytest.raises(ValueError):
            self.connection.write_varint(2147483648)
        with pytest.raises(ValueError):
            self.connection.write_varint(-2147483649)

    def test_readUtf(self):
        self.connection.receive(bytearray.fromhex("0D48656C6C6F2C20776F726C6421"))

        assert self.connection.read_utf() == "Hello, world!"

    def test_writeUtf(self):
        self.connection.write_utf("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("0D48656C6C6F2C20776F726C6421")

    def test_readEmptyUtf(self):
        self.connection.write_utf("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_readAscii(self):
        self.connection.receive(bytearray.fromhex("48656C6C6F2C20776F726C642100"))

        assert self.connection.read_ascii() == "Hello, world!"

    def test_writeAscii(self):
        self.connection.write_ascii("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("48656C6C6F2C20776F726C642100")

    def test_readEmptyAscii(self):
        self.connection.write_ascii("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_readShortNegative(self):
        self.connection.receive(bytearray.fromhex("8000"))

        assert self.connection.read_short() == -32768

    def test_writeShortNegative(self):
        self.connection.write_short(-32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_readShortPositive(self):
        self.connection.receive(bytearray.fromhex("7FFF"))

        assert self.connection.read_short() == 32767

    def test_writeShortPositive(self):
        self.connection.write_short(32767)

        assert self.connection.flush() == bytearray.fromhex("7FFF")

    def test_readUShortPositive(self):
        self.connection.receive(bytearray.fromhex("8000"))

        assert self.connection.read_ushort() == 32768

    def test_writeUShortPositive(self):
        self.connection.write_ushort(32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_readIntNegative(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        assert self.connection.read_int() == -2147483648

    def test_writeIntNegative(self):
        self.connection.write_int(-2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_readIntPositive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFF"))

        assert self.connection.read_int() == 2147483647

    def test_writeIntPositive(self):
        self.connection.write_int(2147483647)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFF")

    def test_readUIntPositive(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        assert self.connection.read_uint() == 2147483648

    def test_writeUIntPositive(self):
        self.connection.write_uint(2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_readLongNegative(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_long() == -9223372036854775808

    def test_writeLongNegative(self):
        self.connection.write_long(-9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    def test_readLongPositive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFFFFFFFFFF"))

        assert self.connection.read_long() == 9223372036854775807

    def test_writeLongPositive(self):
        self.connection.write_long(9223372036854775807)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFFFFFFFFFF")

    def test_readULongPositive(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_ulong() == 9223372036854775808

    def test_writeULongPositive(self):
        self.connection.write_ulong(9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    def test_readBuffer(self):
        self.connection.receive(bytearray.fromhex("027FAA"))
        buffer = self.connection.read_buffer()

        assert buffer.received == bytearray.fromhex("7FAA")
        assert self.connection.flush() == bytearray()

    def test_writeBuffer(self):
        buffer = Connection()
        buffer.write(bytearray.fromhex("7FAA"))
        self.connection.write_buffer(buffer)

        assert self.connection.flush() == bytearray.fromhex("027FAA")


class TCPSocketConnectionTest:
    def setup_method(self):
        socket = Mock()
        socket.recv = Mock()
        socket.send = Mock()
        with patch("socket.create_connection") as create_connection:
            create_connection.return_value = socket
            self.connection = TCPSocketConnection(("localhost", 1234))

    def test_flush(self):
        with pytest.raises(TypeError):
            self.connection.flush()

    def test_receive(self):
        with pytest.raises(TypeError):
            self.connection.receive("")

    def test_remaining(self):
        with pytest.raises(TypeError):
            self.connection.remaining()

    def test_read(self):
        self.connection.socket.recv.return_value = bytearray.fromhex("7FAA")

        assert self.connection.read(2) == bytearray.fromhex("7FAA")

    def test_read_empty(self):
        self.connection.socket.recv.return_value = bytearray.fromhex("")

        with pytest.raises(IOError):
            self.connection.read(2)

    def test_write(self):
        self.connection.write(bytearray.fromhex("7FAA"))

        # pytype: disable=attribute-error
        self.connection.socket.send.assert_called_once_with(bytearray.fromhex("7FAA"))
        # pytype: enable=attribute-error


class UDPSocketConnectionTest:
    def setup_method(self):
        socket = Mock()
        socket.recvfrom = Mock()
        socket.sendto = Mock()
        with patch("socket.socket") as create_socket:
            create_socket.return_value = socket
            self.connection = UDPSocketConnection(("localhost", 1234))

    def test_flush(self):
        with pytest.raises(TypeError):
            self.connection.flush()

    def test_receive(self):
        with pytest.raises(TypeError):
            self.connection.receive("")

    def test_remaining(self):
        assert self.connection.remaining() == 65535

    def test_read(self):
        self.connection.socket.recvfrom.return_value = [bytearray.fromhex("7FAA")]

        assert self.connection.read(2) == bytearray.fromhex("7FAA")

    def test_write(self):
        self.connection.write(bytearray.fromhex("7FAA"))

        # pytype: disable=attribute-error
        self.connection.socket.sendto.assert_called_once_with(bytearray.fromhex("7FAA"), ("localhost", 1234))
        # pytype: enable=attribute-error
