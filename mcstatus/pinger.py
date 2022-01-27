import datetime
import json
import random
from typing import List, Optional, Union

from mcstatus.protocol.connection import Connection, TCPSocketConnection, TCPAsyncSocketConnection

STYLE_MAP = {
    "bold": "l",
    "italic": "o",
    "underlined": "n",
    "obfuscated": "k",
    "color": {
        "dark_red": "4",
        "red": "c",
        "gold": "6",
        "yellow": "e",
        "dark_green": "2",
        "green": "a",
        "aqua": "b",
        "dark_aqua": "3",
        "dark_blue": "1",
        "blue": "9",
        "light_purple": "d",
        "dark_purple": "5",
        "white": "f",
        "gray": "7",
        "dark_gray": "8",
        "black": "0",
    },
}


class ServerPinger:
    def __init__(
        self,
        connection: TCPSocketConnection,
        host: str = "",
        port: int = 0,
        version: int = 47,
        ping_token=None,
    ):
        if ping_token is None:
            ping_token = random.randint(0, (1 << 63) - 1)
        self.version = version
        self.connection = connection
        self.host = host
        self.port = port
        self.ping_token = ping_token

    def handshake(self) -> None:
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.host)
        packet.write_ushort(self.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    def read_status(self) -> "PingResponse":
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
            raise IOError(f"Received invalid status response: {e}")

    def test_ping(self) -> float:
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
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        delta = received - sent
        return delta.total_seconds() * 1000


class AsyncServerPinger(ServerPinger):
    def __init__(
        self, connection: TCPAsyncSocketConnection, host: str = "", port: int = 0, version: int = 47, ping_token=None
    ):
        # We do this to inform python about self.connection type (it's async)
        super().__init__(connection, host=host, port=port, version=version, ping_token=ping_token)  # type: ignore[arg-type]
        self.connection: TCPAsyncSocketConnection

    async def read_status(self) -> "PingResponse":
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
            raise IOError(f"Received invalid status response: {e}")

    async def test_ping(self) -> float:
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
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        delta = received - sent
        return delta.total_seconds() * 1000


class PingResponse:
    # THIS IS SO UNPYTHONIC
    # it's staying just because the tests depend on this structure
    class Players:
        class Player:
            name: str
            id: str

            def __init__(self, raw):
                if not isinstance(raw, dict):
                    raise ValueError(f"Invalid player object (expected dict, found {type(raw)}")

                if "name" not in raw:
                    raise ValueError("Invalid player object (no 'name' value)")
                if not isinstance(raw["name"], str):
                    raise ValueError(f"Invalid player object (expected 'name' to be str, was {type(raw['name'])}")
                self.name = raw["name"]

                if "id" not in raw:
                    raise ValueError("Invalid player object (no 'id' value)")
                if not isinstance(raw["id"], str):
                    raise ValueError(f"Invalid player object (expected 'id' to be str, was {type(raw['id'])}")
                self.id = raw["id"]

        online: int
        max: int
        sample: Optional[List["PingResponse.Players.Player"]]

        def __init__(self, raw):
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid players object (expected dict, found {type(raw)}")

            if "online" not in raw:
                raise ValueError("Invalid players object (no 'online' value)")
            if not isinstance(raw["online"], int):
                raise ValueError(f"Invalid players object (expected 'online' to be int, was {type(raw['online'])})")
            self.online = raw["online"]

            if "max" not in raw:
                raise ValueError("Invalid players object (no 'max' value)")
            if not isinstance(raw["max"], int):
                raise ValueError(f"Invalid players object (expected 'max' to be int, was {type(raw['max'])}")
            self.max = raw["max"]

            if "sample" in raw:
                if not isinstance(raw["sample"], list):
                    raise ValueError(f"Invalid players object (expected 'sample' to be list, was {type(raw['max'])})")
                self.sample = [PingResponse.Players.Player(p) for p in raw["sample"]]
            else:
                self.sample = None

    class Version:
        name: str
        protocol: int

        def __init__(self, raw):
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid version object (expected dict, found {type(raw)})")

            if "name" not in raw:
                raise ValueError("Invalid version object (no 'name' value)")
            if not isinstance(raw["name"], str):
                raise ValueError(f"Invalid version object (expected 'name' to be str, was {type(raw['name'])})")
            self.name = raw["name"]

            if "protocol" not in raw:
                raise ValueError("Invalid version object (no 'protocol' value)")
            if not isinstance(raw["protocol"], int):
                raise ValueError(f"Invalid version object (expected 'protocol' to be int, was {type(raw['protocol'])})")
            self.protocol = raw["protocol"]

    players: Players
    version: Version
    description: str
    favicon: Optional[str]
    latency: float = 0

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
        self.description = self._parse_description(raw["description"])

        self.favicon = raw.get("favicon")

    @staticmethod
    def _parse_description(raw_description: Union[dict, list, str]) -> str:
        if isinstance(raw_description, str):
            return raw_description

        if isinstance(raw_description, dict):
            entries = raw_description.get("extra", [])
            end = raw_description["text"]
        else:
            entries = raw_description
            end = ""

        description = ""

        for entry in entries:
            for style_key, style_val in STYLE_MAP.items():
                if entry.get(style_key):
                    if isinstance(style_val, dict):
                        style_val = style_val[entry[style_key]]

                    description += f"§{style_val}"
            description += entry.get("text", "")

        return description + end
