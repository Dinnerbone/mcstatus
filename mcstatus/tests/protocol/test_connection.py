import socket
from unittest import TestCase
from mock import Mock, patch

from mcstatus.protocol.connection import Connection, TCPSocketConnection


class TestConnection(TestCase):
    def setUp(self):
        self.connection = Connection()

    def test_flush(self):
        self.connection.sent = "\x7F\xAA\xBB"

        self.assertEqual(self.connection.flush(), "\x7F\xAA\xBB")
        self.assertTrue(self.connection.sent == "")

    def test_receive(self):
        self.connection.receive("\x7F")
        self.connection.receive("\xAA\xBB")

        self.assertEqual(self.connection.received, "\x7F\xAA\xBB")

    def test_remaining(self):
        self.connection.receive("\x7F")
        self.connection.receive("\xAA\xBB")

        self.assertEqual(self.connection.remaining(), 3)

    def test_send(self):
        self.connection.write("\x7F")
        self.connection.write("\xAA\xBB")

        self.assertEqual(self.connection.flush(), "\x7F\xAA\xBB")

    def test_read(self):
        self.connection.receive("\x7F\xAA\xBB")

        self.assertEqual(self.connection.read(2), "\x7F\xAA")
        self.assertEqual(self.connection.read(1), "\xBB")

    def test_readSimpleVarInt(self):
        self.connection.receive("\x0F")

        self.assertEqual(self.connection.read_varint(), 15)

    def test_writeSimpleVarInt(self):
        self.connection.write_varint(15)

        self.assertEqual(self.connection.flush(), "\x0F")

    def test_readBigVarInt(self):
        self.connection.receive("\xFF\xFF\xFF\xFF\x7F")

        self.assertEqual(self.connection.read_varint(), 34359738367)

    def test_writeBigVarInt(self):
        self.connection.write_varint(2147483647)

        self.assertEqual(self.connection.flush(), "\xFF\xFF\xFF\xFF\x07")

    def test_readInvalidVarInt(self):
        self.connection.receive("\xFF\xFF\xFF\xFF\x80")

        self.assertRaises(IOError, self.connection.read_varint)

    def test_writeInvalidVarInt(self):
        self.assertRaises(ValueError, self.connection.write_varint, 34359738368)

    def test_readString(self):
        self.connection.receive("\x0D\x48\x65\x6C\x6C\x6F\x2C\x20\x77\x6F\x72\x6C\x64\x21")

        self.assertEqual(self.connection.read_utf(), "Hello, world!")

    def test_writeString(self):
        self.connection.write_utf("Hello, world!")

        self.assertEqual(self.connection.flush(), "\x0D\x48\x65\x6C\x6C\x6F\x2C\x20\x77\x6F\x72\x6C\x64\x21")

    def test_readEmptyString(self):
        self.connection.write_utf("")

        self.assertEqual(self.connection.flush(), "\x00")

    def test_readShortNegative(self):
        self.connection.receive("\x80\x00")

        self.assertEqual(self.connection.read_short(), -32768)

    def test_writeShortNegative(self):
        self.connection.write_short(-32768)

        self.assertEqual(self.connection.flush(), "\x80\x00")

    def test_readShortPositive(self):
        self.connection.receive("\x7F\xFF")

        self.assertEqual(self.connection.read_short(), 32767)

    def test_writeShortPositive(self):
        self.connection.write_short(32767)

        self.assertEqual(self.connection.flush(), "\x7F\xFF")

    def test_readUShortPositive(self):
        self.connection.receive("\x80\x00")

        self.assertEqual(self.connection.read_ushort(), 32768)

    def test_writeUShortPositive(self):
        self.connection.write_ushort(32768)

        self.assertEqual(self.connection.flush(), "\x80\x00")

    def test_readLongNegative(self):
        self.connection.receive("\x80\x00\x00\x00\x00\x00\x00\x00")

        self.assertEqual(self.connection.read_long(), -9223372036854775808)

    def test_writeLongNegative(self):
        self.connection.write_long(-9223372036854775808)

        self.assertEqual(self.connection.flush(), "\x80\x00\x00\x00\x00\x00\x00\x00")

    def test_readLongPositive(self):
        self.connection.receive("\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")

        self.assertEqual(self.connection.read_long(), 9223372036854775807)

    def test_writeLongPositive(self):
        self.connection.write_long(9223372036854775807)

        self.assertEqual(self.connection.flush(), "\x7F\xFF\xFF\xFF\xFF\xFF\xFF\xFF")

    def test_readULongPositive(self):
        self.connection.receive("\x80\x00\x00\x00\x00\x00\x00\x00")

        self.assertEqual(self.connection.read_ulong(), 9223372036854775808)

    def test_writeULongPositive(self):
        self.connection.write_ulong(9223372036854775808)

        self.assertEqual(self.connection.flush(), "\x80\x00\x00\x00\x00\x00\x00\x00")

    def test_readBuffer(self):
        self.connection.receive("\x02\x7F\xAA")
        buffer = self.connection.read_buffer()

        self.assertEqual(buffer.received, "\x7F\xAA")
        self.assertEqual(self.connection.flush(), "")

    def test_writeBuffer(self):
        buffer = Connection()
        buffer.write("\x7F\xAA")
        self.connection.write_buffer(buffer)

        self.assertEqual(self.connection.flush(), "\x02\x7F\xAA")

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
        self.connection.socket.recv.return_value = "\x7F\xAA"

        self.assertEqual(self.connection.read(2), "\x7F\xAA")

    def test_write(self):
        self.connection.write("\x7F\xAA")

        self.connection.socket.send.assert_called_once_with("\x7F\xAA")