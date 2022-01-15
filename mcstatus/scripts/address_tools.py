from urllib.parse import urlparse
from typing import Tuple, Optional, Union
from ipaddress import ip_address


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
