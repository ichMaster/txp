import socket
import threading
import time

import pytest


@pytest.fixture
def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def echo_server(free_port):
    from server.listener import start_listener

    t = threading.Thread(
        target=start_listener,
        args=("127.0.0.1", free_port),
        daemon=True,
    )
    t.start()
    time.sleep(0.3)
    yield "127.0.0.1", free_port
