import asyncio
import asyncssh
import bcrypt
import sys
import random

from typing import Optional, override

with open('/run/secrets/ssh_password', 'r') as f:
    SSH_PASSWORD = bcrypt.hashpw(f.read().strip().encode('utf-8'), bcrypt.gensalt())

class PortListener(asyncssh.SSHListener):
    def __init__(self, conn: asyncssh.SSHServerConnection, client_host: str, client_port: int, server_port: int):
        super().__init__()

        self._conn = conn
        self._client_host = client_host
        self._client_port = client_port
        self._port = server_port

        conn.create_task(self._open_connection())

    async def _open_connection(self):
        reader, writer = await self._conn.open_connection(self._client_host, self._client_port)
        while True:
            await asyncio.sleep(1)
            writer.write(f'random.bittan-ci-proxy.fysiksektionen.se\n')

    def close(self):
        """Stop listening for new connections"""

    async def wait_closed(self):
        """Wait for the listener to close"""

async def handle_client(process: asyncssh.SSHServerProcess) -> None:
    print("Handle client")
    process.stdout.write(f'random.bittan-ci-proxy.fysiksektionen.se\n')
    await process.stdout.drain()
    async for line in process.stdin:
        pass

class LocalhostProxySSHServer(asyncssh.SSHServer):
    def __init__(self):
        self._conn = None

    @override
    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        peername = conn.get_extra_info('peername')[0]
        print(f'SSH connection received from {peername}.')

        self._conn = conn

    @override
    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            print('SSH connection error: ' + str(exc), file=sys.stderr)
        else:
            print('SSH connection closed.')

    @override
    def begin_auth(self, username: str) -> bool:
        return True

    @override
    def password_auth_supported(self) -> bool:
        return True

    @override
    def validate_password(self, username: str, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), SSH_PASSWORD)

    @override
    def server_requested(self, listen_host: str, listen_port: int) -> asyncssh.SSHListener:
        assert self._conn is not None

        port = random.randint(30000, 65535)
        print("Listening on port", port)
        return PortListener(self._conn, listen_host, listen_port, port)

async def start_server() -> None:
    await asyncssh.create_server(LocalhostProxySSHServer, '', 8022,
                                 server_host_keys=['/run/secrets/ssh_host_key'],
                                 process_factory=handle_client)

print('Starting SSH server...')
loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting server: ' + str(exc))

loop.run_forever()
