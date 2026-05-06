# TXP — Architecture & How It Works

## Overview

TXP (Text Transfer Protocol) is a custom text-based protocol for serving Markdown pages over TCP. The system is built incrementally in phases, each adding one architectural layer while keeping the system functional.

The project consists of three main packages:

- **`server/`** — TCP server that listens for connections and processes requests
- **`protocol/`** — Shared data types and serialization (used by both server and client)
- **`client/`** — TUI client for browsing pages (future phases)

## How It Works

### Current State (Phase 0 — TCP Echo)

```
┌──────────────┐         TCP          ┌──────────────────────┐
│   Client     │ ──────────────────── │     TXP Server       │
│  (nc/telnet) │   send bytes         │                      │
│              │ ◄──────────────────── │  Echo: recv → send   │
└──────────────┘   same bytes back    └──────────────────────┘
```

1. Server binds to a TCP port (default 9000)
2. Enters an accept loop waiting for connections
3. On connection: reads data, sends it back verbatim, closes the socket
4. Logs each connection with timestamp, address, and byte count
5. Handles SIGINT/SIGTERM for graceful shutdown

### Target State (Phase 9 — Full System)

```
┌──────────────┐                      ┌──────────────────────────────────────┐
│  TXP Client  │   TXP/1.0 over TCP  │            TXP Server                │
│  (curses TUI)│ ────────────────────▶│                                      │
│              │                      │  listener.py    (accept connections)  │
│  - Navigate  │                      │       │                              │
│  - History   │                      │  connection.py  (per-connection I/O)  │
│  - Bookmarks │                      │       │                              │
│              │                      │  parser.py      (bytes → TxpRequest)  │
│              │◀──────────────────── │       │                              │
│              │   TXP/1.0 response   │  middleware.py  (log, time, errors)   │
└──────────────┘                      │       │                              │
                                      │  router.py      (URL → handler)      │
                                      │       │                              │
                                      │  static.py / handlers                │
                                      │       │                              │
                                      │  renderer.py    (MD → HTML/plain)    │
                                      │       │                              │
                                      │  response.py    (TxpResponse → bytes)│
                                      └──────────────────────────────────────┘
```

## Component Details

### Server Package (`server/`)

| Module | Purpose | Phase |
|--------|---------|-------|
| `cli.py` | Argument parsing, entry point | 0 |
| `listener.py` | TCP bind/listen/accept loop | 0 |
| `connection.py` | Per-connection read/write handler | 0 |
| `parser.py` | Parse raw bytes into `TxpRequest` | 1 |
| `response.py` | Serialize `TxpResponse` to bytes | 1 |
| `static.py` | Serve files from docroot | 2 |
| `renderer.py` | Markdown → HTML/plain conversion | 3 |
| `router.py` | URL pattern → handler dispatch | 4 |
| `middleware.py` | Logging, timing, error handling chain | 6 |
| `config.py` | Configuration management | 9 |

### Protocol Package (`protocol/`)

| Module | Purpose | Phase |
|--------|---------|-------|
| `__init__.py` | Package root, version string | 0 |
| `request.py` | `TxpRequest` dataclass | 1 |
| `response.py` | `TxpResponse` dataclass | 1 |
| `status.py` | `StatusCode` enum (200, 301, 400, 403, 404, 500) | 1 |
| `headers.py` | `parse_headers()` / `serialize_headers()` | 1 |

### Client Package (`client/`)

| Module | Purpose | Phase |
|--------|---------|-------|
| `cli.py` | Argument parsing, entry point | 0 |
| `connection.py` | TCP client connection | 8 |
| `parser.py` | Parse response bytes | 8 |
| `tui.py` | Curses terminal UI | 8 |
| `history.py` | Back/forward navigation | 8 |
| `bookmarks.py` | Persistent bookmarks | 8 |

## TXP/1.0 Protocol Wire Format

### Request

```
METHOD /path TXP/1.0\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

**Methods:** `GET`, `POST`, `HEAD`, `INFO`

### Response

```
TXP/1.0 CODE TEXT\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

**Status codes:** 200 OK, 301 Moved, 400 Bad Request, 403 Forbidden, 404 Not Found, 500 Server Error

## Request Lifecycle (Target)

```
raw bytes in
    │
    ▼
parser.py ──── malformed? ──── 400 Bad Request
    │
    ▼
TxpRequest
    │
    ▼
middleware chain (log → timer → error)
    │
    ▼
router.py ──── no match? ──── 404 Not Found
    │
    ▼
handler (static / dynamic)
    │
    ▼
TxpResponse
    │
    ▼
response.py
    │
    ▼
raw bytes out
```

## Entry Points

| Command | Module | Description |
|---------|--------|-------------|
| `txp-server` | `server.cli:main_server` | Console script (installed via pip) |
| `txp-client` | `client.cli:main_client` | Console script (installed via pip) |
| `python txp_server.py` | `server.cli:main_server` | Legacy script |
| `python txp_client.py` | `client.cli:main_client` | Legacy script |

## Configuration

CLI arguments with defaults:

```
txp-server --host 0.0.0.0 --port 9000 --docroot ./content --verbose
txp-client txp://localhost:9000/
```

Full config file support (`txp.conf`) arrives in Phase 9.

## Implementation Phases

| Phase | Name | What It Adds |
|-------|------|-------------|
| 0 | TCP Echo | Socket bind, accept loop, echo, shutdown, logging |
| 1 | Protocol Layer | Request/response parsing and serialization |
| 2 | Static File Server | Serve .md files from docroot |
| 3 | Content Negotiation | Markdown → HTML/plain rendering |
| 4 | Router | URL pattern matching, dynamic handlers |
| 5 | POST & Forms | Form processing, guestbook demo |
| 6 | Middleware | Logging, timing, error handling chain |
| 7 | Concurrency | Threaded, select, asyncio models |
| 8 | TUI Client | Curses browser with navigation |
| 9 | Configuration | Config file, PID file, daemon mode |

## Dependencies

- **Python 3.11+** (required)
- **Standard library only** through Phase 2 (`socket`, `signal`, `argparse`, `datetime`, `os`, `pathlib`)
- **`mistune` or `markdown`** added in Phase 3 for HTML rendering
- **Dev:** `pytest>=7.0`, `pytest-cov>=4.0`
