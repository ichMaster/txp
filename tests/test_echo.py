import socket
import threading
import time

import pytest


class TestEcho:
    def test_echo_basic(self, echo_server):
        host, port = echo_server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(b"Hello TXP")
            data = s.recv(4096)
        assert data == b"Hello TXP"

    def test_echo_multibyte_utf8(self, echo_server):
        host, port = echo_server
        payload = "Привет TXP".encode("utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(payload)
            data = s.recv(4096)
        assert data == payload

    def test_empty_connection(self, echo_server):
        host, port = echo_server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        time.sleep(0.2)

    def test_multiple_sequential_connections(self, echo_server):
        host, port = echo_server
        for i in range(3):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                msg = f"Message {i}".encode()
                s.sendall(msg)
                data = s.recv(4096)
                assert data == msg

    def test_large_payload(self, echo_server):
        host, port = echo_server
        payload = b"X" * 4096
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(payload)
            data = s.recv(8192)
        assert data == payload

    def test_port_in_use(self, echo_server):
        host, port = echo_server
        with pytest.raises(OSError):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
            finally:
                s.close()
