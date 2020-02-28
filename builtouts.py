TUNNEL_PORT = 0x7474
SERVER_PORT = 0x7473
CLIENT_PORT = 0x7463


async def read(reader):
    data = await reader.read(n=1024)
    if not data:
        raise EOFError
    return data


async def readline(reader):
    data = await reader.readline()
    if not data:
        raise EOFError
    return data


async def readexactly(reader, n):
    data = await reader.readexactly(n)
    if len(data) < n:
        raise EOFError
    return data


def write(writer, data):
    if writer.is_closing():
        raise EOFError
    writer.write(data)


async def close(writer):
    await writer.drain()
    writer.close()
