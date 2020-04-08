import socket

def ip_type(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return 4 if address.count('.') == 3 else None
    except socket.error:
        try:
          socket.inet_pton(socket.AF_INET6, address)
          return 6
        except socket.error:
          return None
    return 4

def parse_address(address):
    parts = address.split(":")
    if len(parts) == 1:
        return (address, None)
    elif len(parts) == 2:
        try:
            return (parts[0], int(parts[1]))
        except:
            raise ValueError("Invalid address '%s'" % address)
    elif len(parts) < 10:
        tmp = address
        port = None

        if len(parts[0]) and len(parts[-2]) and "[" == parts[0][0] and "]" == parts[-2][-1] :
            if not parts[-1].isdigit():
                raise ValueError("Invalid address '%s'" % address)

            port = int(parts[-1])
            parts[0] = parts[0][1:]
            parts[-2] = parts[-2][:-1]
            tmp = ':'.join(parts[0:-1])

        if not ip_type(tmp) == 6:
            raise ValueError("Invalid address '%s'" % address)
        else:
            return (tmp, port)
        parts[0] = parts[0][1:]
        parts[-2] = parts[0][:-1]

    else:
        raise ValueError("Invalid address '%s'" % address)