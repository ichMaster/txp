# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TXP (Text Transfer Protocol) — a custom text-based protocol and server/client system for serving Markdown pages over TCP. Python 3.11+, stdlib-only until Phase 3 (which adds `mistune` or `markdown`).

## Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Console scripts (available after pip install -e)
txp-server --help
txp-server --port 9000 --docroot ./content
txp-client txp://localhost:9000/

# Run tests
pytest
pytest tests/test_parser.py              # single file
pytest tests/test_parser.py::test_name   # single test
pytest -v                                # verbose

# Manual testing (before client exists)
echo -e "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n" | nc localhost 9000
```

## Architecture

Three packages, shared protocol layer:

- **`protocol/`** — Pure data types shared by server and client. No I/O. `TxpRequest`/`TxpResponse` dataclasses, `StatusCode` enum, header parse/serialize utilities.
- **`server/`** — TCP listener → connection handler → middleware chain → router → handlers (static file serving, dynamic routes). Three concurrency models: threaded, select, asyncio.
- **`client/`** — TCP connection + curses TUI with link navigation, history stack, bookmarks.

Request lifecycle: `raw bytes → parser.py → TxpRequest → middleware → router → handler → TxpResponse → response.py → raw bytes`

## TXP/1.0 Wire Format

```
GET /path TXP/1.0\r\n
Header: Value\r\n
\r\n
[body]
```

Response: `TXP/1.0 CODE TEXT\r\n` + headers + `\r\n` + body. Methods: `GET`, `POST`, `HEAD`, `INFO`. Content negotiation via `Accept` header: `text/markdown` (default), `text/html`, `text/plain`.

## Implementation Phases

The project is built incrementally across phases 0–9. Each phase must leave the system functional. See `specifications/ROADMAP.md` for the full plan and `specifications/roadmap/phase-N-issues.md` for issue breakdowns.

Current phase issues follow the format from `specifications/roadmap/phase-1-issues.md`: summary table, dependency tree, per-issue description/tasks/acceptance criteria.

## Security Constraints (Phase 2+)

- Path traversal: canonicalize with `os.path.realpath()`, reject outside docroot
- Request limits: 8KB headers, 1MB body, 30s idle timeout
- No directory listing — 403 for directories without `index.md`

## Specifications

All project specifications live in `specifications/`:
- `TXP-Server-Specification-EN.md` — protocol definition and full phase descriptions
- `ARCHITECTURE.md` — component architecture, data flows, dependency map
- `ROADMAP.md` — phased implementation plan with LOC estimates and dependency timeline
- `roadmap/phase-N-issues.md` — issue breakdowns per phase
- `roadmap/phase-N-tasks.md` — granular task tables per phase
