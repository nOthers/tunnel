import asyncio
from builtouts import *


async def forward(reader, writer):
    while True:
        try:
            write(writer, await read(reader))
        except EOFError:
            break
    await close(writer)


def create_server(host, uuid, port):
    async def cb(reader, writer):
        be_reader, be_writer = await asyncio.open_connection(host, CLIENT_PORT)
        write(be_writer, f'{uuid}:{port}'.encode() + b'\n')
        asyncio.ensure_future(forward(reader, be_writer))
        asyncio.ensure_future(forward(be_reader, writer))
    return cb


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('uuid', help='Unique ID of the device')
    parser.add_argument('portables', nargs='*', help='Port tables for mapping, such as "80" or "80:8080"')
    args = parser.parse_args()
    import os
    tunnel_host = os.environ.get('TUNNEL_HOST', '0.0.0.0')
    for pp in args.portables:
        if ':' not in pp:
            pp = pp + ':' + pp
        remote_port, local_port, = pp.split(':')
        asyncio.ensure_future(asyncio.start_server(create_server(tunnel_host, args.uuid, remote_port), port=local_port))
    asyncio.get_event_loop().run_forever()
