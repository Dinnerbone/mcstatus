from __future__ import annotations

from ipaddress import ip_address
from typing import Optional, Tuple, Union
from urllib.parse import urlparse


def ip_type(address: Union[int, str]) -> Optional[int]:
    try:
        return ip_address(address).version
    except ValueError:
        return None


def parse_address(address: str) -> Tuple[str, Optional[int]]:
    tmp = urlparse("//" + address)
    if not tmp.hostname:
        raise ValueError(f"Invalid address '{address}'")
    return (tmp.hostname, tmp.port)
