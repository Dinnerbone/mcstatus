import socket
from urllib.parse import urlparse
from ipaddress import ip_address


def ip_type(address):
    try:
        return ip_address(address).version
    except ValueError:
        return None


def parse_address(address):
    tmp = urlparse("//" + address)
    if not tmp.hostname:
        raise ValueError("Invalid address '%s'" % address)
    return (tmp.hostname, tmp.port)
