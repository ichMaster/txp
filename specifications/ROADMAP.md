# TXP/1.0 -- Implementation Roadmap

**Version:** 1.0
**Based on:** TXP-Server-Specification-EN v1.0
**Status:** Draft

---

## Overview

10-phase incremental build of a text server and TUI client using the custom TXP/1.0 protocol. Each phase produces a working system. Estimated total: ~1420 LOC of Python.

---

## Phase 0: TCP Echo (Foundation)

**Goal:** Verify TCP connectivity end-to-end.

**Files created:**
- `txp_server.py` -- entry point
- `server/__init__.py`
- `server/listener.py` -- bind, listen, accept

**Tasks:**
- [ ] TCP listener on configurable port (default 9000)
- [ ] Accept loop with graceful shutdown (SIGINT/SIGTERM)
- [ ] Echo handler: read -> write back -> close connection
- [ ] Connection logging to stdout

**Verification:**
```bash
echo "Hello TXP" | nc localhost 9000
# Output: Hello TXP
```

**Estimate:** ~50 LOC | Dependencies: stdlib only (`socket`, `signal`)

---

## Phase 1: Protocol Layer

**Goal:** Parse TXP/1.0 requests and build structured responses.

**Files created:**
- `protocol/__init__.py`
- `protocol/request.py` -- `TxpRequest` dataclass
- `protocol/response.py` -- `TxpResponse` dataclass
- `protocol/status.py` -- `StatusCode` enum
- `protocol/headers.py` -- `parse_headers()`, `serialize_headers()`
- `server/parser.py` -- raw bytes -> `TxpRequest`
- `server/response.py` -- `TxpResponse` -> raw bytes
- `tests/test_parser.py`
- `tests/test_protocol.py`

**Tasks:**
- [ ] Define `TxpRequest` dataclass (method, path, version, headers, body)
- [ ] Define `TxpResponse` dataclass (status_code, status_text, headers, body)
- [ ] Implement `StatusCode` enum (200, 301, 400, 403, 404, 500)
- [ ] Implement header parser and serializer
- [ ] Implement request parser: first line + headers + body
- [ ] Implement response serializer with proper `\r\n` formatting
- [ ] Unit tests: valid request, malformed request, missing headers

**Verification:**
```
Input:  "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n"
Output: TxpRequest(method='GET', path='/index.md', version='1.0',
                   headers={'Host': 'localhost'}, body=None)
```

**Estimate:** ~120 LOC + tests | Cumulative: ~170 LOC

---

## Phase 2: Static File Server

**Goal:** Serve Markdown files from a document root directory.

**Files created:**
- `server/static.py` -- path resolution, file reading, response building
- `server/config.py` -- docroot, host, port settings
- `server/connection.py` -- integrate parser + static + response builder
- `content/index.md`
- `content/about.md`
- `content/links.md`
- `content/404.md`

**Tasks:**
- [ ] Config module: docroot, host, port (from file or CLI args)
- [ ] Path resolution: URL path -> filesystem path within docroot
- [ ] Path traversal protection: canonicalize, reject `../` outside docroot
- [ ] `GET /path.md` -> read file -> 200 with `Content-Type: text/markdown`
- [ ] `GET /` -> rewrite to `GET /index.md`
- [ ] `GET /missing.md` -> 404 with `content/404.md` body
- [ ] `HEAD` support: headers only, no body
- [ ] Set `Content-Length` header on all responses
- [ ] Reject directory access without `index.md` (403)

**Verification:**
```bash
echo -e "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n" | nc localhost 9000
# TXP/1.0 200 OK
# Content-Type: text/markdown
# Content-Length: ...
```

**Estimate:** ~150 LOC + content files | Cumulative: ~320 LOC

---

## Phase 3: Content Negotiation & Rendering

**Goal:** Deliver content in the format requested via the `Accept` header.

**Files created:**
- `server/renderer.py` -- MD -> HTML, MD -> plain text
- `tests/test_renderer.py`

**Tasks:**
- [ ] Markdown -> HTML renderer (using `mistune` or `markdown` library)
- [ ] Markdown -> plain text renderer (strip markup via regex)
- [ ] `Accept` header parser with format priorities
- [ ] Content negotiation: match Accept to available formats
- [ ] Set `Content-Type` response header to match selected format
- [ ] Fallback: no `Accept` header -> `text/markdown`
- [ ] HTML template with minimal inline CSS
- [ ] Unit tests for each rendering path

**Verification:**
```bash
# HTML
echo -e "GET /index.md TXP/1.0\r\nAccept: text/html\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/html

# Plain text
echo -e "GET /index.md TXP/1.0\r\nAccept: text/plain\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/plain
```

**Estimate:** ~100 LOC | Cumulative: ~420 LOC | New dependency: `mistune` or `markdown`

---

## Phase 4: Router & Custom Handlers

**Goal:** Route requests to Python handler functions, not just static files.

**Files created:**
- `server/router.py` -- URL pattern matching, handler registry
- `tests/test_router.py`

**Tasks:**
- [ ] Router class: `register(method, pattern, handler_fn)`
- [ ] Pattern matching: exact paths + simple wildcards (`/docs/*`)
- [ ] Handler signature: `(request: TxpRequest) -> TxpResponse`
- [ ] Priority: exact match > wildcard > catch-all
- [ ] Built-in route: `INFO /` -> server info (name, version, uptime, page count)
- [ ] Built-in route: `GET /sitemap` -> dynamic list of all `.md` files
- [ ] Built-in route: `GET /*` -> static file handler (catch-all)
- [ ] Return 404 for unmatched paths
- [ ] Return 405 Method Not Allowed for mismatched methods
- [ ] Unit tests for pattern matching and resolution

**Verification:**
```python
router = Router()
router.add("GET", "/sitemap", sitemap_handler)
router.add("INFO", "/", server_info_handler)
router.add("GET", "/*", static_handler)

handler = router.resolve("GET", "/sitemap")
# -> sitemap_handler
```

**Estimate:** ~100 LOC | Cumulative: ~520 LOC

---

## Phase 5: POST & Form Processing

**Goal:** Handle POST requests with URL-encoded form data.

**Files created:**
- Guestbook handler (within server or as a separate module)
- `content/guestbook.md` (template)

**Tasks:**
- [ ] Body parser: `key=value&key2=value2` -> dict
- [ ] URL-decode values
- [ ] POST handler framework integrated with router
- [ ] Guestbook feature:
  - `GET /guestbook` -> render entries + form
  - `POST /guestbook` -> validate, append entry, redirect 301 -> `GET /guestbook`
- [ ] State persistence: `guestbook.json` file
- [ ] Form syntax convention in Markdown:
  ```
  ---form action=/guestbook method=POST
  Name: [name]
  Message: [message]
  [submit:Sign]
  ---
  ```
- [ ] Integration tests for the full POST -> redirect -> GET flow

**Estimate:** ~150 LOC | Cumulative: ~670 LOC

---

## Phase 6: Middleware Chain

**Goal:** Add composable request/response processing layers.

**Files created:**
- `server/middleware.py`
- `content/500.md` -- custom error page

**Tasks:**
- [ ] Middleware signature: `(handler) -> handler` (decorator pattern)
- [ ] `LogMiddleware`: log `[timestamp] METHOD /path -> STATUS (Xms)`
- [ ] `ErrorMiddleware`: catch unhandled exceptions -> 500 with `content/500.md`
- [ ] `TimerMiddleware`: measure processing time, add `X-Response-Time` header
- [ ] Configurable chain order in setup
- [ ] Compose: `app = LogMiddleware(TimerMiddleware(ErrorMiddleware(router.dispatch)))`
- [ ] Unit tests for each middleware in isolation and composed

**Estimate:** ~80 LOC | Cumulative: ~750 LOC

---

## Phase 7: Concurrency

**Goal:** Serve multiple clients simultaneously with three concurrency models.

**Files modified:**
- `server/listener.py` -- add threaded, select, and async implementations

**Files created:**
- `bench.py` -- benchmark script

**Tasks:**
- [ ] `ThreadedListener`: accept -> submit to `ThreadPoolExecutor`
- [ ] `SelectListener`: non-blocking sockets + `select()` event loop
- [ ] `AsyncListener`: `asyncio.start_server` with async handlers
- [ ] Config option: `concurrency_model = threaded | select | async`
- [ ] Connection limit enforcement (`max_connections`)
- [ ] Benchmark script: N concurrent connections, M requests, measure throughput
- [ ] Compare results across all three models

**Benchmark target:**
```
python bench.py --connections 50 --requests 200
# threaded:  ~180 req/s
# select:    ~220 req/s
# async:     ~250 req/s
```

**Estimate:** ~200 LOC (three implementations) | Cumulative: ~950 LOC

---

## Phase 8: TUI Client

**Goal:** Build a full-featured terminal client with page browsing.

**Files created:**
- `txp_client.py` -- entry point
- `client/__init__.py`
- `client/connection.py` -- TCP connect, send, receive
- `client/parser.py` -- response parser
- `client/tui.py` -- curses-based terminal UI
- `client/history.py` -- back/forward navigation stack
- `client/bookmarks.py` -- bookmark persistence

**Tasks:**
- [ ] TCP client: connect to host:port, send `TxpRequest`, receive `TxpResponse`
- [ ] Curses TUI with three-panel layout:
  - Address bar (top): `txp://host:port/path`
  - Content area (center): rendered Markdown
  - Status bar (bottom): status code, content-type, response time
- [ ] Terminal Markdown rendering:
  - Headings -> bold + color
  - Bold -> bold attribute
  - Italic -> dim/underline
  - Code -> reverse video
  - Links -> highlighted, navigable
  - Lists -> preserved as-is
- [ ] Link navigation: Tab/Shift-Tab to cycle, Enter to follow
- [ ] History stack with Backspace for back navigation
- [ ] Manual URL entry (`g` key)
- [ ] Bookmarks: `b` to list, `B` to save, stored in `~/.txp/bookmarks.json`
- [ ] Quit with `q`
- [ ] URL scheme: `txp://host:port/path`

**Estimate:** ~350 LOC | Cumulative: ~1300 LOC | Dependencies: `curses` (stdlib)

---

## Phase 9: Configuration & Polish

**Goal:** Production-ready configuration, signals, and structured logging.

**Files created/modified:**
- `txp.conf` -- TOML configuration file
- `server/config.py` -- enhanced with TOML parsing and CLI args

**Tasks:**
- [ ] TOML config file parser (`txp.conf`)
- [ ] CLI arguments via `argparse` with config file override
- [ ] Configuration precedence: CLI args > config file > defaults
- [ ] Graceful shutdown: SIGINT/SIGTERM -> finish active connections, then exit
- [ ] Config reload: SIGHUP -> re-read `txp.conf` without restart
- [ ] PID file: write to `/tmp/txp.pid` on start, remove on shutdown
- [ ] Structured logging with configurable level and output file
- [ ] Optional `--daemon` mode
- [ ] Full integration test suite

**Estimate:** ~120 LOC | Cumulative: ~1420 LOC

---

## Progress Tracker

| Phase | Description                   | LOC   | Cumulative | Status      |
|-------|-------------------------------|-------|------------|-------------|
| 0     | TCP Echo                      | ~50   | ~50        | Not started |
| 1     | Protocol Layer                | ~120  | ~170       | Not started |
| 2     | Static File Server            | ~150  | ~320       | Not started |
| 3     | Content Negotiation           | ~100  | ~420       | Not started |
| 4     | Router & Handlers             | ~100  | ~520       | Not started |
| 5     | POST & Forms                  | ~150  | ~670       | Not started |
| 6     | Middleware Chain               | ~80   | ~750       | Not started |
| 7     | Concurrency                   | ~200  | ~950       | Not started |
| 8     | TUI Client                    | ~350  | ~1300      | Not started |
| 9     | Configuration & Polish        | ~120  | ~1420      | Not started |

---

## Dependency Timeline

```
Phase 0 -----> Phase 1 -----> Phase 2 -----> Phase 3
  TCP            Protocol       Static         Rendering
  Echo           Layer          Server

                                  |
                                  v
                               Phase 4 -----> Phase 5
                                Router         POST/Forms

                                                  |
                                                  v
                                               Phase 6 -----> Phase 7
                                                Middleware      Concurrency

Phase 1 ----------------------------------------> Phase 8
  Protocol (shared)                                TUI Client

Phase 2 + 7 -----------------------------------> Phase 9
  Config                                           Polish
```

**Critical path:** 0 -> 1 -> 2 -> 4 -> 5 -> 6 -> 7 -> 9

**Parallel tracks (after Phase 2):**
- Phase 3 (Rendering) can proceed independently after Phase 2
- Phase 8 (Client) can begin after Phase 1, but full testing requires Phase 2+

---

## External Dependencies

| Package              | Purpose                    | Required From |
|----------------------|----------------------------|---------------|
| Python 3.11+         | Runtime                    | Phase 0       |
| `mistune` or `markdown` | Markdown -> HTML        | Phase 3       |
| stdlib: `socket`     | TCP networking             | Phase 0       |
| stdlib: `signal`     | Graceful shutdown          | Phase 0       |
| stdlib: `select`     | Non-blocking I/O           | Phase 7       |
| stdlib: `asyncio`    | Async concurrency          | Phase 7       |
| stdlib: `curses`     | Terminal UI                | Phase 8       |
| stdlib: `argparse`   | CLI argument parsing       | Phase 9       |
| stdlib: `tomllib`    | TOML config parsing (3.11+)| Phase 9       |

---

## Post-MVP Extensions (Phase 10+)

| Extension           | Description                                        |
|---------------------|----------------------------------------------------|
| TLS support         | `ssl.wrap_socket` for `txps://` scheme             |
| Virtual hosts       | Multiple docroots via `Host` header                |
| Caching             | ETag/If-None-Match, 304 Not Modified               |
| Plugin system       | Load handlers from Python modules via config       |
| Backlinks index     | Track which pages link to each page                |
| Full-text search    | Search across all content in docroot               |
| Live reload         | Persistent connection, push on file change         |
| Compression         | Gzip with `Accept-Encoding` negotiation            |
