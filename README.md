# TXP — Text Transfer Protocol

A custom text-based protocol and server/client system for serving Markdown pages over TCP. Built from scratch in Python 3.11+ using only the standard library.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

Start the server:

```bash
txp-server
txp-server --port 8080
txp-server --host 127.0.0.1 --port 9000 --docroot ./content
```

Test with netcat (Phase 0 — echo mode):

```bash
echo "Hello TXP" | nc localhost 9000
# Output: Hello TXP
```

## Running Tests

```bash
pytest
pytest -v              # verbose
pytest --cov=server    # with coverage
```

## Project Structure

```
txp/
  server/          # TCP listener, connection handler, CLI
  protocol/        # Shared data types (request, response, status codes)
  client/          # TUI client (future)
  content/         # Markdown pages served by the server
  tests/           # pytest suite
  txp_server.py    # Legacy entry point
  txp_client.py    # Legacy entry point
```

## Current Status

**Phase 0 (TCP Echo) — Complete**

The server accepts TCP connections and echoes data back. Graceful shutdown via Ctrl+C, connection logging to stdout.
