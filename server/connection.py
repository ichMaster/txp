from datetime import datetime


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def handle_connection(client_socket, client_address):
    addr, port = client_address
    print(f"[{_timestamp()}] Connection from {addr}:{port}")

    try:
        data = client_socket.recv(4096)
        if not data:
            print(f"[{_timestamp()}] Client {addr}:{port} disconnected")
            return
        client_socket.sendall(data)
        print(f"[{_timestamp()}] Echoed {len(data)} bytes to {addr}:{port}")
    finally:
        client_socket.close()
