import signal
import socket
import sys
from datetime import datetime

from server.connection import handle_connection

_shutdown = False


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def start_listener(host: str, port: int, handler=None):
    global _shutdown
    _shutdown = False

    if handler is None:
        handler = handle_connection

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
    except OSError as e:
        print(f"Error: cannot bind to {host}:{port} — {e}", file=sys.stderr)
        sys.exit(1)

    server_socket.listen(5)
    print(f"Listening on {host}:{port}")

    def _signal_handler(signum, frame):
        global _shutdown
        _shutdown = True
        print(f"\n[{_timestamp()}] Shutting down...")
        server_socket.close()

    import threading
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not _shutdown:
            try:
                client_socket, client_address = server_socket.accept()
            except OSError:
                break
            handler(client_socket, client_address)
    finally:
        try:
            server_socket.close()
        except OSError:
            pass
        print(f"[{_timestamp()}] Server stopped")
