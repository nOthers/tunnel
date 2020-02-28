import json
import asyncio
import prettytable
from builtouts import *


async def connect(host):
    reader, writer = await asyncio.open_connection(host, TUNNEL_PORT)
    row = 0
    while True:
        status = json.loads((await readline(reader)).decode().strip())
        for i in range(row):
            print('\x1b[A\x1b[K', end='')
        row = 4
        table = prettytable.PrettyTable()
        table.field_names = ['uuid', 'port', 'using', 'used', ]
        for uuid in sorted(status.keys()):
            users = status[uuid]['users']
            if not users:
                table.add_row([uuid, '', '', '', ])
                row += 1
            else:
                for port in sorted(users.keys()):
                    using = len(users[port]['using'])
                    used = users[port]['used']
                    table.add_row([uuid, port, using, used, ])
                    row += 1
                    uuid = ''
        print(table)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    import os
    tunnel_host = os.environ.get('TUNNEL_HOST', '0.0.0.0')
    asyncio.get_event_loop().run_until_complete(connect(tunnel_host))
