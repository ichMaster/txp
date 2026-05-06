# Phase 0 — Issues

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | TXP-001 | Project scaffold and server entry point | S | 1 — Scaffold | -- |
| 2 | TXP-002 | TCP listener and accept loop | S | 2 — Networking | TXP-001 |
| 3 | TXP-003 | Echo handler, graceful shutdown, and connection logging | S | 3 — Handler | TXP-002 |
| 4 | TXP-004 | Phase 0 unit and integration tests | S | 4 — Testing | TXP-003 |

**Size legend:** S = 1–2 days, M = 3–5 days, L = 5–8 days

---

## Dependency Tree

```
    TXP-001 (scaffold)
        |
    TXP-002 (listener)
        |
    TXP-003 (echo + shutdown + logging)
        |
    TXP-004 (tests)
```

**Parallelization hints:**

- This phase is strictly sequential — each issue builds on the previous
- Phase 0 is the foundation for all subsequent phases; it must be complete before Phase 1 begins

---

## Stage 1 — Scaffold

### TXP-001 — Project scaffold and server entry point

**Description:**
Set up the project skeleton with packaging, CLI entry points, and the package structure needed for the server, protocol, client, tests, and content directories. The developer experience must match `bi-converter` from `modernization-demo`: editable install via `pip install -e ".[dev]"`, registered console scripts (`txp-server`, `txp-client`) on PATH with auto-generated `--help` and `--version`, and pytest preconfigured.

**What needs to be done:**

**Packaging (`pyproject.toml`):**
- Create `pyproject.toml` with `setuptools>=68.0` + `wheel` build backend
- Project name: `txp`, version: `0.1.0`, requires-python: `>=3.11`
- No runtime dependencies (stdlib only until Phase 3)
- Dev optional dependencies: `pytest>=7.0`, `pytest-cov>=4.0`
- Console script entry points:
  - `txp-server = "server.cli:main_server"`
  - `txp-client = "client.cli:main_client"`
- Package discovery: `setuptools.packages.find` with `where=["."]`, `include=["server*", "protocol*", "client*"]`
- Pytest config: `[tool.pytest.ini_options]` with `testpaths = ["tests"]`

**Package structure:**
- Create `server/` package with `__init__.py`
- Create `protocol/` package with `__init__.py` containing `__version__ = "0.1.0"`
- Create `client/` package with `__init__.py`
- Create `tests/` directory with `__init__.py`
- Create `content/` directory (empty, for Phase 2 content files)

**Server CLI (`server/cli.py`):**
- `build_parser() -> argparse.ArgumentParser` with `prog="txp-server"`
- `--version` flag reading from `protocol.__version__`
- `--host` (default `0.0.0.0`), `--port`/`-p` (default `9000`, type int)
- `--docroot`/`-d` (default `./content`), `--config`/`-c` (config file path)
- `--verbose`/`-v` (enable detailed logging)
- `main_server(argv)` entry point: parse args, print startup banner, return 0

**Client CLI (`client/cli.py`):**
- `build_parser() -> argparse.ArgumentParser` with `prog="txp-client"`
- `--version` flag reading from `protocol.__version__`
- `url` positional argument (default `txp://localhost:9000/`)
- `--verbose`/`-v`
- `main_client(argv)` entry point: parse args, print connection message, return 0

**Legacy entry points:**
- `txp_server.py` — delegates to `server.cli.main_server()`
- `txp_client.py` — delegates to `client.cli.main_client()`

**Dependencies:** None

**Expected result:**
A clean project skeleton that installs and imports correctly. After `pip install -e ".[dev]"`, `txp-server` and `txp-client` are available as console commands with working `--help`, `--version`, and tab completion.

**Acceptance criteria:**
- [ ] `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"` exits 0
- [ ] `txp-server --help` prints full usage with all flags
- [ ] `txp-server --version` prints `txp-server 0.1.0`
- [ ] `txp-server` prints startup banner and exits (no listener yet)
- [ ] `txp-server --port 8080` accepts port argument
- [ ] `txp-client --help` prints usage
- [ ] `txp-client --version` prints `txp-client 0.1.0`
- [ ] `python txp_server.py --help` works (legacy entry point)
- [ ] `import server`, `import protocol`, `import client` work without errors
- [ ] `pytest` runs clean (0 tests collected, no errors)
- [ ] Directory layout matches the target structure from the specification

---

## Stage 2 — Networking

### TXP-002 — TCP listener and accept loop

**Description:**
Implement the TCP server socket that binds to a configurable address, listens for incoming connections, and runs an accept loop. This is the core networking foundation — all future request handling flows through this accept loop.

**What needs to be done:**
- In `server/listener.py`, implement `start_listener(host: str, port: int)`:
  - Create TCP socket (`socket.AF_INET`, `socket.SOCK_STREAM`)
  - Set `SO_REUSEADDR` option to allow quick restarts
  - Bind to `(host, port)`
  - Listen with a backlog of 5
  - Print `Listening on {host}:{port}`
  - Enter accept loop:
    - `socket.accept()` -> `(client_socket, client_address)`
    - Pass connection to handler (placeholder: just close socket)
    - Continue accepting
- Wire `txp_server.py` to call `start_listener(host, port)` after argument parsing
- Handle `OSError` on bind (port already in use) — print clear error and exit with code 1

**Dependencies:** TXP-001

**Expected result:**
A TCP server that binds, listens, and accepts connections. Connections are accepted but not yet handled (just closed immediately).

**Acceptance criteria:**
- [ ] `txp-server` binds to `0.0.0.0:9000` and prints listening message
- [ ] `txp-server --port 8080` binds to port 8080
- [ ] `nc localhost 9000` connects successfully (connection accepted)
- [ ] Server continues accepting after a client disconnects
- [ ] Binding to an in-use port prints a clear error and exits with code 1
- [ ] `SO_REUSEADDR` set — server restarts immediately after stop

---

## Stage 3 — Handler

### TXP-003 — Echo handler, graceful shutdown, and connection logging

**Description:**
Complete the TCP echo server by adding the connection handler (read data, echo it back, close), graceful shutdown via SIGINT/SIGTERM, and connection logging to stdout. After this issue, the system passes the Phase 0 acceptance test.

**What needs to be done:**

**Echo handler:**
- In `server/connection.py`, implement `handle_connection(client_socket, client_address)`:
  - Receive data from client (`socket.recv(4096)`)
  - If data is empty (client disconnected), close socket and return
  - Send received data back to client (`socket.sendall(data)`)
  - Close client socket
- Wire the handler into the accept loop in `server/listener.py`

**Graceful shutdown:**
- Register signal handlers for `SIGINT` and `SIGTERM` in `server/listener.py`
- On signal: set a shutdown flag, close the server socket, print `Shutting down...`
- Accept loop checks shutdown flag and exits cleanly
- Ensure no orphaned sockets on shutdown (close server socket in `finally` block)

**Connection logging:**
- Log each accepted connection: `[{timestamp}] Connection from {address}:{port}`
- Log each completed echo: `[{timestamp}] Echoed {n} bytes to {address}:{port}`
- Log disconnection (empty recv): `[{timestamp}] Client {address}:{port} disconnected`
- Log shutdown: `[{timestamp}] Server stopped`
- Timestamp format: `YYYY-MM-DD HH:MM:SS`
- All logging to stdout

**Dependencies:** TXP-002

**Expected result:**
A fully functional TCP echo server with clean shutdown and visible connection activity. Passes the Phase 0 acceptance test.

**Acceptance criteria:**
- [ ] `echo "Hello TXP" | nc localhost 9000` outputs `Hello TXP`
- [ ] Multiple sequential connections work (accept loop continues)
- [ ] Ctrl+C triggers graceful shutdown with `Shutting down...` message
- [ ] No socket errors or tracebacks on shutdown
- [ ] Each connection logged with timestamp, address, and byte count
- [ ] Empty connection (client connects and disconnects) handled without crash
- [ ] Server socket closed in `finally` block — no resource leak

---

## Stage 4 — Testing

### TXP-004 — Phase 0 unit and integration tests

**Description:**
Write pytest tests covering all Phase 0 components: CLI argument parsing, TCP listener, echo handler, and graceful shutdown. Tests must be automated — no manual `nc` required. The server is started in a background thread and tested via socket connections from the test process.

**What needs to be done:**

**`tests/conftest.py` — shared fixtures:**
- `free_port` fixture: find an available TCP port for test isolation
- `echo_server` fixture: start server in a background thread on `free_port`, yield `(host, port)`, shut down after test

**`tests/test_cli.py` — CLI argument parsing tests:**
- Test default arguments: host `0.0.0.0`, port `9000`, docroot `./content`
- Test `--port 8080` overrides default
- Test `--host 127.0.0.1` overrides default
- Test `--docroot /tmp/pages` overrides default
- Test `--version` outputs version string
- Test `--help` exits 0

**`tests/test_echo.py` — echo server integration tests:**
- Test echo: send `b"Hello TXP"`, receive `b"Hello TXP"` back
- Test echo with multibyte UTF-8 data (e.g., Cyrillic)
- Test empty connection: connect and immediately close — no crash
- Test multiple sequential connections on the same server
- Test large payload (4096 bytes) echoed correctly
- Test server refuses bind on occupied port (start two servers on same port)

**Dependencies:** TXP-003

**Expected result:**
A complete pytest suite that validates the echo server without manual intervention. All tests pass with `pytest`.

**Acceptance criteria:**
- [ ] `pytest tests/test_cli.py` passes — all CLI parsing tests green
- [ ] `pytest tests/test_echo.py` passes — all echo integration tests green
- [ ] Tests are isolated: each test gets its own port, no conflicts
- [ ] No manual `nc`/`telnet` required — fully automated
- [ ] `pytest` runs clean with no warnings
- [ ] `pytest --cov=server` shows coverage for listener and connection modules

---

## Phase 0 scope notes

**Total effort:** ~1–2 days for a single developer.

**Critical path:** TXP-001 → TXP-002 → TXP-003 → TXP-004 (strictly sequential)

**Dependencies:** stdlib only (`socket`, `signal`, `argparse`, `datetime`)

**LOE:** ~30–50 lines of application code

**Acceptance test (end of phase):**
```bash
echo "Hello TXP" | nc localhost 9000
# Output: Hello TXP
```

**Companion documents:**
- `phase-0-tasks.md` — detailed task tables per stage
- `ARCHITECTURE.md` — listener and connection handler architecture
- `ROADMAP.md` — full phase overview and dependency timeline
- `TXP-Server-Specification-EN.md` — Phase 0 specification
