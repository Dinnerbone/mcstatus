from unittest import TestCase

from mock import Mock, patch

from mcstatus.protocol.connection import Connection, TCPSocketConnection, UDPSocketConnection


class TestConnection(TestCase):
    def setUp(self):
        self.connection = Connection()

    def test_flush(self):
        self.connection.sent = bytearray.fromhex("7FAABB")

        self.assertEqual(self.connection.flush(), bytearray.fromhex("7FAABB"))
        self.assertTrue(self.connection.sent == "")

    def test_receive(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        self.assertEqual(self.connection.received, bytearray.fromhex("7FAABB"))

    def test_remaining(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        self.assertEqual(self.connection.remaining(), 3)

    def test_send(self):
        self.connection.write(bytearray.fromhex("7F"))
        self.connection.write(bytearray.fromhex("AABB"))

        self.assertEqual(self.connection.flush(), bytearray.fromhex("7FAABB"))

    def test_read(self):
        self.connection.receive(bytearray.fromhex("7FAABB"))

        self.assertEqual(self.connection.read(2), bytearray.fromhex("7FAA"))
        self.assertEqual(self.connection.read(1), bytearray.fromhex("BB"))

    def test_readSimpleVarInt(self):
        self.connection.receive(bytearray.fromhex("0F"))

        self.assertEqual(self.connection.read_varint(), 15)

    def test_writeSimpleVarInt(self):
        self.connection.write_varint(15)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("0F"))

    def test_readBigVarInt(self):
        self.connection.receive(bytearray.fromhex("FFFFFFFF7F"))

        self.assertEqual(self.connection.read_varint(), 34359738367)

    def test_writeBigVarInt(self):
        self.connection.write_varint(2147483647)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("FFFFFFFF07"))

    def test_readInvalidVarInt(self):
        self.connection.receive(bytearray.fromhex("FFFFFFFF80"))

        self.assertRaises(IOError, self.connection.read_varint)

    def test_writeInvalidVarInt(self):
        self.assertRaises(ValueError, self.connection.write_varint, 34359738368)

    def test_readUtf(self):
        self.connection.receive(bytearray.fromhex("0D48656C6C6F2C20776F726C6421"))

        self.assertEqual(self.connection.read_utf(), "Hello, world!")

    def test_writeUtf(self):
        self.connection.write_utf("Hello, world!")

        self.assertEqual(self.connection.flush(), bytearray.fromhex("0D48656C6C6F2C20776F726C6421"))

    def test_readEmptyUtf(self):
        self.connection.write_utf("")

        self.assertEqual(self.connection.flush(), bytearray.fromhex("00"))

    def test_readAscii(self):
        self.connection.receive(bytearray.fromhex("48656C6C6F2C20776F726C642100"))

        self.assertEqual(self.connection.read_ascii(), "Hello, world!")

    def test_writeAscii(self):
        self.connection.write_ascii("Hello, world!")

        self.assertEqual(self.connection.flush(), bytearray.fromhex("48656C6C6F2C20776F726C642100"))

    def test_readEmptyAscii(self):
        self.connection.write_ascii("")

        self.assertEqual(self.connection.flush(), bytearray.fromhex("00"))

    def test_readShortNegative(self):
        self.connection.receive(bytearray.fromhex("8000"))

        self.assertEqual(self.connection.read_short(), -32768)

    def test_writeShortNegative(self):
        self.connection.write_short(-32768)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("8000"))

    def test_readShortPositive(self):
        self.connection.receive(bytearray.fromhex("7FFF"))

        self.assertEqual(self.connection.read_short(), 32767)

    def test_writeShortPositive(self):
        self.connection.write_short(32767)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("7FFF"))

    def test_readUShortPositive(self):
        self.connection.receive(bytearray.fromhex("8000"))

        self.assertEqual(self.connection.read_ushort(), 32768)

    def test_writeUShortPositive(self):
        self.connection.write_ushort(32768)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("8000"))

    def test_readIntNegative(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        self.assertEqual(self.connection.read_int(), -2147483648)

    def test_writeIntNegative(self):
        self.connection.write_int(-2147483648)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("80000000"))

    def test_readIntPositive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFF"))

        self.assertEqual(self.connection.read_int(), 2147483647)

    def test_writeIntPositive(self):
        self.connection.write_int(2147483647)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("7FFFFFFF"))

    def test_readUIntPositive(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        self.assertEqual(self.connection.read_uint(), 2147483648)

    def test_writeUIntPositive(self):
        self.connection.write_uint(2147483648)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("80000000"))

    def test_readLongNegative(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        self.assertEqual(self.connection.read_long(), -9223372036854775808)

    def test_writeLongNegative(self):
        self.connection.write_long(-9223372036854775808)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("8000000000000000"))

    def test_readLongPositive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFFFFFFFFFF"))

        self.assertEqual(self.connection.read_long(), 9223372036854775807)

    def test_writeLongPositive(self):
        self.connection.write_long(9223372036854775807)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("7FFFFFFFFFFFFFFF"))

    def test_readULongPositive(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        self.assertEqual(self.connection.read_ulong(), 9223372036854775808)

    def test_writeULongPositive(self):
        self.connection.write_ulong(9223372036854775808)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("8000000000000000"))

    def test_readBuffer(self):
        self.connection.receive(bytearray.fromhex("027FAA"))
        buffer = self.connection.read_buffer()

        self.assertEqual(buffer.received, bytearray.fromhex("7FAA"))
        self.assertEqual(self.connection.flush(), bytearray())

    def test_writeBuffer(self):
        buffer = Connection()
        buffer.write(bytearray.fromhex("7FAA"))
        self.connection.write_buffer(buffer)

        self.assertEqual(self.connection.flush(), bytearray.fromhex("027FAA"))


class TCPSocketConnectionTest(TestCase):
    def setUp(self):
        socket = Mock()
        socket.recv = Mock()
        socket.send = Mock()
        with patch("socket.create_connection") as create_connection:
            create_connection.return_value = socket
            self.connection = TCPSocketConnection(("localhost", 1234))

    def test_flush(self):
        self.assertRaises(TypeError, self.connection.flush)

    def test_receive(self):
        self.assertRaises(TypeError, self.connection.receive, "")

    def test_remaining(self):
        self.assertRaises(TypeError, self.connection.remaining)

    def test_read(self):
        self.connection.socket.recv.return_value = bytearray.fromhex("7FAA")

        self.assertEqual(self.connection.read(2), bytearray.fromhex("7FAA"))

    def test_read_empty(self):
        self.connection.socket.recv.return_value = bytearray.fromhex("")

        with self.assertRaises(IOError):
            self.connection.read(2)

    def test_write(self):
        self.connection.write(bytearray.fromhex("7FAA"))

        self.connection.socket.send.assert_called_once_with(bytearray.fromhex("7FAA"))


class UDPSocketConnectionTest(TestCase):
    def setUp(self):
        socket = Mock()
        socket.recvfrom = Mock()
        socket.sendto = Mock()
        with patch("socket.socket") as create_socket:
            create_socket.return_value = socket
            self.connection = UDPSocketConnection(("localhost", 1234))

    def test_flush(self):
        self.assertRaises(TypeError, self.connection.flush)

    def test_receive(self):
        self.assertRaises(TypeError, self.connection.receive, "")

    def test_remaining(self):
        self.assertEqual(self.connection.remaining(), 65535)

    def test_read(self):
        self.connection.socket.recvfrom.return_value = [bytearray.fromhex("7FAA")]

        self.assertEqual(self.connection.read(2), bytearray.fromhex("7FAA"))

    def test_write(self):
        self.connection.write(bytearray.fromhex("7FAA"))

        self.connection.socket.sendto.assert_called_once_with(bytearray.fromhex("7FAA"), ("localhost", 1234))