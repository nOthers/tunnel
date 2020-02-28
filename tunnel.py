import json
import time
import asyncio
import itertools
from builtouts import *
UNIQUE = itertools.count(1)
TUNNEL_STORE = []
CLIENT_STORE = {}
SERVER_STORE = {}


class Status(dict):
    def set_server(self, serverID):
        self[serverID] = {
            'users': {},
            'time': int(time.time() * 1000),
        }
        self.notify_all()

    def del_server(self, serverID):
        if serverID in self:
            del self[serverID]
        self.notify_all()

    def set_client(self, clientID, serverID, port):
        if serverID in self:
            if port not in self[serverID]['users']:
                self[serverID]['users'][port] = {
                    'using': [],
                    'used': 0,
                }
            self[serverID]['users'][port]['using'].append(clientID)
            self[serverID]['users'][port]['used'] += 1
        self.notify_all()

    def del_client(self, clientID):
        for server in self.values():
            for client in server['users'].values():
                if clientID in client['using']:
                    client['using'].remove(clientID)
        self.notify_all()

    def notify_all(self):
        for writer in TUNNEL_STORE:
            self.notify_one(writer)

    def notify_one(self, writer):
        write(writer, json.dumps(self).encode() + b'\n')


STATUS = Status()


async def tunnel_cb(reader, writer):
    try:
        STATUS.notify_one(writer)
        TUNNEL_STORE.append(writer)
        try:
            while True:
                await read(reader)
        finally:
            TUNNEL_STORE.remove(writer)
    except EOFError:
        pass
    finally:
        await close(writer)


async def server_cb(reader, writer):
    try:
        serverID = (await readline(reader)).decode().strip()
        SERVER_STORE[serverID] = writer
        STATUS.set_server(serverID)
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
            if SERVER_STORE.get(serverID) is writer:
                del SERVER_STORE[serverID]
                STATUS.del_server(serverID)
    except EOFError:
        pass
    finally:
        await close(writer)


async def client_cb(reader, writer):
    try:
        serverID, port, = (await readline(reader)).decode().strip().rsplit(':', 1)
        if serverID in SERVER_STORE:
            be_writer = SERVER_STORE[serverID]
            clientID = str(next(UNIQUE))
            CLIENT_STORE[clientID] = writer
            STATUS.set_client(clientID, serverID, port)
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
                STATUS.del_client(clientID)
                write(be_writer, clientID.encode() + b'\n')
                write(be_writer, b'close\n')
    except EOFError:
        pass
    finally:
        await close(writer)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    asyncio.ensure_future(asyncio.start_server(tunnel_cb, port=TUNNEL_PORT))
    asyncio.ensure_future(asyncio.start_server(server_cb, port=SERVER_PORT))
    asyncio.ensure_future(asyncio.start_server(client_cb, port=CLIENT_PORT))
    asyncio.get_event_loop().run_forever()
