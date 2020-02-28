import asyncio
from builtouts import *


async def wrap(clientID, reader, writer):
    try:
        while True:
            data = await read(reader)
            write(writer, clientID.encode() + b'\n')
            write(writer, str(len(data)).encode() + b'\n')
            write(writer, data)
    except EOFError:
        pass


async def link(host, uuid, wlan):
    reader, writer = await asyncio.open_connection(host, SERVER_PORT)
    write(writer, uuid.encode() + b'\n')
    writer_store = {}
    while True:
        clientID = (await readline(reader)).decode().strip()
        action = (await readline(reader)).decode().strip()
        if action == 'open':
            port = int((await readline(reader)).decode().strip())
            try:
                be_reader, be_writer = await asyncio.open_connection(wlan, port)
            except ConnectionError:
                pass
            else:
                writer_store[clientID] = be_writer
                asyncio.ensure_future(wrap(clientID, be_reader, writer))
                del be_reader, be_writer
        elif action == 'message':
            n = int((await readline(reader)).decode().strip())
            data = await readexactly(reader, n)
            if clientID in writer_store:
                writer_store[clientID].write(data)
        elif action == 'close':
            if clientID in writer_store:
                await close(writer_store[clientID])
                del writer_store[clientID]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('wlan', help='Network address of the device')
    parser.add_argument('uuid', help='Unique ID of the device')
    args = parser.parse_args()
    import os
    tunnel_host = os.environ.get('TUNNEL_HOST', '0.0.0.0')
    asyncio.get_event_loop().run_until_complete(link(tunnel_host, args.uuid, args.wlan))
