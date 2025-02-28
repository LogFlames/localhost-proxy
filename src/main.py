import asyncio
import asyncssh
import bcrypt
import sys
import random
import uuid
import os
from typing import Optional, override

from nginx import create_nginx_conf, disable_nginx_proxy

if not os.path.exists('/run/secrets/ssh_password'):
    print("No SSH PASSWRD secret found. Exiting.")
    sys.exit(1)

with open('/run/secrets/ssh_password', 'r') as f:
    SSH_PASSWORD = bcrypt.hashpw(f.read().strip().encode('utf-8'), bcrypt.gensalt())

if "DOMAIN" not in os.environ:
    print("DOMAIN environment variable not set. Exiting.")
    sys.exit(1)

if "PROTOCOL" not in os.environ:
    print("PROTOCOL environment variable not set. Exiting.")
    sys.exit(1)

DOMAIN = os.environ["DOMAIN"]
PROTOCOL = os.environ["PROTOCOL"]

async def get_port(process: asyncssh.SSHServerProcess):
    for _ in range(100): # timeout after 10 seconds
        await asyncio.sleep(0.1)
        conn = process.channel.get_connection()
        if not conn:
            continue
        if "custom_forward_port" not in dir(conn):
            continue
        return conn.custom_forward_port
    return None

async def read_infinite(process: asyncssh.SSHServerProcess) -> None:
    try:
        async for line in process.stdin:
            if not line:
                break
    except asyncssh.BreakReceived:
        pass

async def handle_client(process: asyncssh.SSHServerProcess) -> None:
    await process.stdout.drain()

    read = asyncio.create_task(read_infinite(process))

    port = await get_port(process)

    if port is None:
        process.stdout.write("Timed out waiting for port.\n")
        process.exit(1)

    uid = str(uuid.uuid4())
    # Create NGINX config
    nginx_domain = DOMAIN.format(uid)
    create_nginx_conf(nginx_domain, port)
    process.stdout.write(PROTOCOL + "://" + nginx_domain + "\n")

    await read

    if port is not None:
        disable_nginx_proxy(nginx_domain)
        pass

    process.exit(0)

def wrap_forward_local_port(conn):
    original_method = conn.forward_local_port
    def forward_local_port(listen_host: str, listen_port: int, dest_host: str, dest_port: int, accept_handler: Optional[asyncssh.SSHAcceptHandler] = None) -> asyncssh.SSHListener:
        if (listen_host, listen_port) == (dest_host, dest_port):
            listen_port = random.randint(10000, 65535)
            conn.custom_forward_port = listen_port 
        print(f'Forwarding local port {listen_host}:{listen_port} to {dest_host}:{dest_port}')
        return original_method(listen_host, listen_port, dest_host, dest_port, accept_handler)
    conn.forward_local_port = forward_local_port

class LocalhostProxySSHServer(asyncssh.SSHServer):
    def __init__(self):
        self._conn = None

    @override
    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        peername = conn.get_extra_info('peername')[0]
        print(f'SSH connection received from {peername}.')

        self._conn = conn
        wrap_forward_local_port(self._conn)

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
    def server_requested(self, listen_host: str, listen_port: int) -> bool:
        return True

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
