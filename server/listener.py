import socket
import sys


def start_listener(host: str, port: int, handler=None):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
    except OSError as e:
        print(f"Error: cannot bind to {host}:{port} — {e}", file=sys.stderr)
        sys.exit(1)

    server_socket.listen(5)
    print(f"Listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            if handler:
                handler(client_socket, client_address)
            else:
                client_socket.close()
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()
