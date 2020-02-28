#!/usr/local/bin/python3
import asyncio
import itertools
from builtouts import *
UNIQUE = itertools.count(1)
CLIENT_STORE = {}
SERVER_STORE = {}


async def client_cb(reader, writer):
    try:
        serverID, port, = (await readline(reader)).decode().strip().rsplit(':', 1)
        if serverID in SERVER_STORE:
            be_writer = SERVER_STORE[serverID]
            clientID = str(next(UNIQUE))
            CLIENT_STORE[clientID] = writer
            write(be_writer, clientID.encode() + b'\n')
            write(be_writer, b'open\n')
            write(be_writer, port.encode() + b'\n')
            try:
                while True:
                    data = await read(reader)
                    write(be_writer, clientID.encode() + b'\n')
                    write(be_writer, b'message\n')
                    write(be_writer, str(len(data)).encode() + b'\n')
                    write(be_writer, data)
            finally:
                del CLIENT_STORE[clientID]
                write(be_writer, clientID.encode() + b'\n')
                write(be_writer, b'close\n')
    except EOFError:
        pass
    finally:
        await close(writer)


async def server_cb(reader, writer):
    try:
        serverID = (await readline(reader)).decode().strip()
        SERVER_STORE[serverID] = writer
        try:
            while True:
                clientID = (await readline(reader)).decode().strip()
                n = int((await readline(reader)).decode().strip())
                data = await readexactly(reader, n)
                if clientID in CLIENT_STORE:
                    try:
                        write(CLIENT_STORE[clientID], data)
                    except EOFError:
                        pass
        finally:
            if SERVER_STORE.get(serverID) is write:
                del SERVER_STORE[serverID]
    except EOFError:
        pass
    finally:
        await close(writer)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    asyncio.ensure_future(asyncio.start_server(client_cb, port=CLIENT_PORT))
    asyncio.ensure_future(asyncio.start_server(server_cb, port=SERVER_PORT))
    asyncio.get_event_loop().run_forever()
