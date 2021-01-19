import datetime
import json
import random
from six import string_types

from mcstatus.protocol.connection import Connection


class ServerPinger:
    def __init__(self, connection, host="", port=0, version=47, ping_token=None):
        if ping_token is None:
            ping_token = random.randint(0, (1 << 63) - 1)
        self.version = version
        self.connection = connection
        self.host = host
        self.port = port
        self.ping_token = ping_token

    def handshake(self):
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.host)
        packet.write_ushort(self.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    def read_status(self):
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw)
        except ValueError as e:
            raise IOError("Received invalid status response: %s" % e)

    def test_ping(self):
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        received = datetime.datetime.now()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError("Received mangled ping response packet (expected token %d, received %d)" % (
                self.ping_token, received_token))

        delta = (received - sent)
        # We have no trivial way of getting a time delta :(
        return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000.0

class AsyncServerPinger(ServerPinger):
    async def read_status(self):
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw)
        except ValueError as e:
            raise IOError("Received invalid status response: %s" % e)

    async def test_ping(self):
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        received = datetime.datetime.now()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError("Received mangled ping response packet (expected token %d, received %d)" % (
                self.ping_token, received_token))

        delta = (received - sent)
        # We have no trivial way of getting a time delta :(
        return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000.0

class PingResponse:
    class Players:
        class Player:
            def __init__(self, raw):
                if not isinstance(raw, dict):
                    raise ValueError("Invalid player object (expected dict, found %s" % type(raw))

                if "name" not in raw:
                    raise ValueError("Invalid player object (no 'name' value)")
                if not isinstance(raw["name"], string_types):
                    raise ValueError("Invalid player object (expected 'name' to be str, was %s)" % type(raw["name"]))
                self.name = raw["name"]

                if "id" not in raw:
                    raise ValueError("Invalid player object (no 'id' value)")
                if not isinstance(raw["id"], string_types):
                    raise ValueError("Invalid player object (expected 'id' to be str, was %s)" % type(raw["id"]))
                self.id = raw["id"]

        def __init__(self, raw):
            if not isinstance(raw, dict):
                raise ValueError("Invalid players object (expected dict, found %s" % type(raw))

            if "online" not in raw:
                raise ValueError("Invalid players object (no 'online' value)")
            if not isinstance(raw["online"], int):
                raise ValueError("Invalid players object (expected 'online' to be int, was %s)" % type(raw["online"]))
            self.online = raw["online"]

            if "max" not in raw:
                raise ValueError("Invalid players object (no 'max' value)")
            if not isinstance(raw["max"], int):
                raise ValueError("Invalid players object (expected 'max' to be int, was %s)" % type(raw["max"]))
            self.max = raw["max"]

            if "sample" in raw:
                if not isinstance(raw["sample"], list):
                    raise ValueError("Invalid players object (expected 'sample' to be list, was %s)" % type(raw["max"]))
                self.sample = [PingResponse.Players.Player(p) for p in raw["sample"]]
            else:
                self.sample = None

    class Version:
        def __init__(self, raw):
            if not isinstance(raw, dict):
                raise ValueError("Invalid version object (expected dict, found %s" % type(raw))

            if "name" not in raw:
                raise ValueError("Invalid version object (no 'name' value)")
            if not isinstance(raw["name"], string_types):
                raise ValueError("Invalid version object (expected 'name' to be str, was %s)" % type(raw["name"]))
            self.name = raw["name"]

            if "protocol" not in raw:
                raise ValueError("Invalid version object (no 'protocol' value)")
            if not isinstance(raw["protocol"], int):
                raise ValueError("Invalid version object (expected 'protocol' to be int, was %s)" % type(raw["protocol"]))
            self.protocol = raw["protocol"]

    def __init__(self, raw):
        self.raw = raw

        if "players" not in raw:
            raise ValueError("Invalid status object (no 'players' value)")
        self.players = PingResponse.Players(raw["players"])

        if "version" not in raw:
            raise ValueError("Invalid status object (no 'version' value)")
        self.version = PingResponse.Version(raw["version"])

        if "description" not in raw:
            raise ValueError("Invalid status object (no 'description' value)")
        self.description = raw["description"]

        if "favicon" in raw:
            self.favicon = raw["favicon"]
        else:
            self.favicon = None

        self.latency = None
