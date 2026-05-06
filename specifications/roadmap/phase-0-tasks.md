# Phase 0 — TCP Echo Tasks

## 1. Scaffold

### 1.1 Packaging (`pyproject.toml`)

| # | Task | Issue |
|---|------|-------|
| 1 | Create `pyproject.toml` with `setuptools>=68.0` + `wheel` build backend | TXP-001 |
| 2 | Set project name `txp`, version `0.1.0`, requires-python `>=3.11` | TXP-001 |
| 3 | Add `[project.optional-dependencies]` dev extra: `pytest>=7.0`, `pytest-cov>=4.0` | TXP-001 |
| 4 | Register console scripts: `txp-server = "server.cli:main_server"`, `txp-client = "client.cli:main_client"` | TXP-001 |
| 5 | Configure `[tool.setuptools.packages.find]` with `where=["."]`, `include=["server*", "protocol*", "client*"]` | TXP-001 |
| 6 | Configure `[tool.pytest.ini_options]` with `testpaths = ["tests"]` | TXP-001 |

### 1.2 Package structure

| # | Task | Issue |
|---|------|-------|
| 1 | Create `server/` package with `__init__.py` | TXP-001 |
| 2 | Create `protocol/` package with `__init__.py` containing `__version__ = "0.1.0"` | TXP-001 |
| 3 | Create `client/` package with `__init__.py` | TXP-001 |
| 4 | Create `tests/` directory with `__init__.py` | TXP-001 |
| 5 | Create `content/` directory (empty, for Phase 2) | TXP-001 |

### 1.3 Server CLI (`server/cli.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `build_parser()` returning `argparse.ArgumentParser` with `prog="txp-server"` | TXP-001 |
| 2 | Add `--version` flag reading from `protocol.__version__` | TXP-001 |
| 3 | Add `--host` argument (default `0.0.0.0`) | TXP-001 |
| 4 | Add `--port`/`-p` argument (default 9000, type int) | TXP-001 |
| 5 | Add `--docroot`/`-d` argument (default `./content`) | TXP-001 |
| 6 | Add `--config`/`-c` argument (config file path) | TXP-001 |
| 7 | Add `--verbose`/`-v` flag | TXP-001 |
| 8 | Implement `main_server(argv)` entry point: parse args, print startup banner, return 0 | TXP-001 |

### 1.4 Client CLI (`client/cli.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `build_parser()` returning `argparse.ArgumentParser` with `prog="txp-client"` | TXP-001 |
| 2 | Add `--version` flag reading from `protocol.__version__` | TXP-001 |
| 3 | Add `url` positional argument (default `txp://localhost:9000/`) | TXP-001 |
| 4 | Add `--verbose`/`-v` flag | TXP-001 |
| 5 | Implement `main_client(argv)` entry point: parse args, print connection message, return 0 | TXP-001 |

### 1.5 Legacy entry points

| # | Task | Issue |
|---|------|-------|
| 1 | Create `txp_server.py` — delegates to `server.cli.main_server()` | TXP-001 |
| 2 | Create `txp_client.py` — delegates to `client.cli.main_client()` | TXP-001 |

---

## 2. TCP Listener

### 2.1 Server socket (`server/listener.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Create TCP socket with `socket.AF_INET`, `socket.SOCK_STREAM` | TXP-002 |
| 2 | Set `SO_REUSEADDR` option for quick restarts | TXP-002 |
| 3 | Bind to `(host, port)` | TXP-002 |
| 4 | Listen with backlog of 5 | TXP-002 |
| 5 | Print `Listening on {host}:{port}` | TXP-002 |

### 2.2 Accept loop (`server/listener.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement accept loop: `socket.accept()` -> `(client_socket, client_address)` | TXP-002 |
| 2 | Pass accepted connection to handler (placeholder: close socket) | TXP-002 |
| 3 | Handle `OSError` on bind — print error and exit with code 1 | TXP-002 |

### 2.3 Integration (`server/cli.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Wire `main_server()` to call `start_listener(args.host, args.port)` after argument parsing | TXP-002 |

---

## 3. Echo Handler and Shutdown

### 3.1 Echo handler (`server/connection.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `handle_connection(client_socket, client_address)` | TXP-003 |
| 2 | Receive data with `socket.recv(4096)` | TXP-003 |
| 3 | Handle empty data (client disconnected): close socket, return | TXP-003 |
| 4 | Echo data back with `socket.sendall(data)` | TXP-003 |
| 5 | Close client socket after echo | TXP-003 |
| 6 | Wire handler into accept loop in `server/listener.py` | TXP-003 |

### 3.2 Graceful shutdown (`server/listener.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Register signal handler for `SIGINT` | TXP-003 |
| 2 | Register signal handler for `SIGTERM` | TXP-003 |
| 3 | On signal: set shutdown flag, close server socket | TXP-003 |
| 4 | Accept loop checks shutdown flag and exits cleanly | TXP-003 |
| 5 | Close server socket in `finally` block — no resource leak | TXP-003 |
| 6 | Print `Shutting down...` on signal | TXP-003 |

### 3.3 Connection logging

| # | Task | Issue |
|---|------|-------|
| 1 | Log accepted connection: `[{timestamp}] Connection from {address}:{port}` | TXP-003 |
| 2 | Log completed echo: `[{timestamp}] Echoed {n} bytes to {address}:{port}` | TXP-003 |
| 3 | Log disconnection: `[{timestamp}] Client {address}:{port} disconnected` | TXP-003 |
| 4 | Log shutdown: `[{timestamp}] Server stopped` | TXP-003 |
| 5 | Timestamp format: `YYYY-MM-DD HH:MM:SS` | TXP-003 |

---

## 4. Unit and Integration Tests

### 4.1 Test fixtures (`tests/conftest.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `free_port` fixture: find an available TCP port for test isolation | TXP-004 |
| 2 | Implement `echo_server` fixture: start server in background thread on `free_port`, yield `(host, port)`, shut down after test | TXP-004 |

### 4.2 CLI argument parsing tests (`tests/test_cli.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Test default arguments: host `0.0.0.0`, port `9000`, docroot `./content` | TXP-004 |
| 2 | Test `--port 8080` overrides default | TXP-004 |
| 3 | Test `--host 127.0.0.1` overrides default | TXP-004 |
| 4 | Test `--docroot /tmp/pages` overrides default | TXP-004 |
| 5 | Test `--version` outputs version string | TXP-004 |
| 6 | Test `--help` exits 0 | TXP-004 |

### 4.3 Echo server integration tests (`tests/test_echo.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Test echo: send `b"Hello TXP"`, receive `b"Hello TXP"` back | TXP-004 |
| 2 | Test echo with multibyte UTF-8 data (e.g., Cyrillic) | TXP-004 |
| 3 | Test empty connection: connect and immediately close — no crash | TXP-004 |
| 4 | Test multiple sequential connections on the same server | TXP-004 |
| 5 | Test large payload (4096 bytes) echoed correctly | TXP-004 |
| 6 | Test server refuses bind on occupied port | TXP-004 |
