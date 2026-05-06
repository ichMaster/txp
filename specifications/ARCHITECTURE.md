# TXP/1.0 -- Architecture Document

**Version:** 1.0
**Based on:** TXP-Server-Specification-EN v1.0
**Status:** Draft

---

## 1. System Overview

TXP (Text Transfer Protocol) is a custom text-based protocol for serving Markdown pages over TCP. The system consists of two primary components: a **server** that serves, routes, and renders Markdown content, and a **TUI client** that provides terminal-based browsing with navigation, history, and bookmarks.

```
+-------------------+        TXP/1.0 over TCP        +-------------------+
|                   | <-----------------------------> |                   |
|    TXP Client     |    GET /page.md TXP/1.0\r\n    |    TXP Server     |
|    (TUI/curses)   |    TXP/1.0 200 OK\r\n          |    (Python 3.11+) |
|                   |                                 |                   |
+-------------------+                                 +-------------------+
```

---

## 2. High-Level Architecture

```
                          +---------------------------+
                          |      txp_server.py        |
                          |      (Entry Point)        |
                          +------------+--------------+
                                       |
                          +------------v--------------+
                          |      config.py            |
                          |  (txp.conf / CLI args)    |
                          +------------+--------------+
                                       |
                          +------------v--------------+
                          |      listener.py          |
                          |  TCP bind/accept loop     |
                          |  (threaded|select|async)  |
                          +------------+--------------+
                                       |
                          +------------v--------------+
                          |      connection.py        |
                          |  Per-connection handler    |
                          +------------+--------------+
                                       |
                          +------------v--------------+
                          |    Middleware Chain        |
                          |  log -> timer -> error    |
                          +------------+--------------+
                                       |
                     +-----------------v-----------------+
                     |           router.py               |
                     |  URL pattern -> handler dispatch  |
                     +------+----------+---------+-------+
                            |          |         |
               +------------+   +------+------+  +------------+
               |  Dynamic       |  static.py  |  |  POST      |
               |  Handlers      |  File serve |  |  Handlers  |
               |  (info,sitemap)|             |  |  (forms)   |
               +----------------+------+------+  +------------+
                                       |
                          +------------v--------------+
                          |      renderer.py          |
                          |  MD -> HTML | plain | raw |
                          +---------------------------+
```

---

## 3. Component Architecture

### 3.1 Protocol Layer (`protocol/`)

The protocol layer defines the data structures and serialization rules for TXP/1.0. It is shared between server and client and has no I/O dependencies.

| Module       | Responsibility                          | Key Types                        |
|--------------|-----------------------------------------|----------------------------------|
| `request.py` | Request data model                      | `TxpRequest` dataclass           |
| `response.py`| Response data model                     | `TxpResponse` dataclass          |
| `status.py`  | Status code definitions                 | `StatusCode` enum                |
| `headers.py` | Header parsing and serialization        | `parse_headers()`, `serialize_headers()` |

**Data flow:**

```
Raw bytes --> parse_headers() --> TxpRequest
TxpResponse --> serialize_headers() --> Raw bytes
```

**TxpRequest fields:** method, path, version, headers (dict), body (optional)
**TxpResponse fields:** status_code, status_text, headers (dict), body

### 3.2 Server Core (`server/`)

#### listener.py -- TCP Listener

Manages the server socket lifecycle: bind, listen, accept. Supports three concurrency models selected via configuration:

| Model      | Implementation          | Characteristics                    |
|------------|-------------------------|------------------------------------|
| `threaded` | `ThreadPoolExecutor`    | Simple, OS-level concurrency       |
| `select`   | `select.select()` loop  | Single-thread, non-blocking I/O    |
| `async`    | `asyncio.start_server`  | Coroutine-based, highest throughput|

All models enforce `max_connections` from config.

#### connection.py -- Connection Handler

Reads raw bytes from socket, delegates to parser, passes `TxpRequest` through the middleware chain, and writes the serialized `TxpResponse` back. Enforces:

- 30s idle timeout
- 8KB max header size
- 1MB max body size

#### parser.py -- Request Parser

Parses the request line (`METHOD /path TXP/1.0`), headers, and optional body. Returns `TxpRequest` on success or a 400 `TxpResponse` on malformed input.

#### response.py -- Response Builder

Serializes `TxpResponse` into wire format:

```
TXP/1.0 {code} {text}\r\n
{Header}: {Value}\r\n
\r\n
{body}
```

Automatically sets `Content-Length`, `Date`, and `Server` headers.

#### router.py -- Request Router

Maps `(method, path_pattern)` to handler functions. Resolution order:

1. Exact match (`GET /sitemap`)
2. Wildcard match (`GET /docs/*`)
3. Catch-all (`GET /*` -- static file handler)

Handler signature: `(request: TxpRequest) -> TxpResponse`

Returns 404 if no pattern matches, 405 if the path matches but method does not.

#### static.py -- Static File Server

Resolves URL paths to filesystem paths within the configured `docroot`.

**Security model:**
- Canonicalize path via `os.path.realpath()`
- Reject any resolved path outside docroot (prevents `../` traversal)
- Return 403 for directory requests without `index.md`
- No directory listing

**Request handling:**
- `GET /path.md` -> read file, return 200 with body
- `GET /` -> rewrite to `GET /index.md`
- `HEAD /path.md` -> return headers only, no body
- Missing file -> 404 with `content/404.md`

#### renderer.py -- Content Renderer

Transforms Markdown source based on the `Accept` header:

| Accept Header    | Output          | Library           |
|------------------|-----------------|-------------------|
| `text/markdown`  | Raw Markdown    | None (passthrough)|
| `text/html`      | HTML document   | `mistune`/`markdown` |
| `text/plain`     | Stripped text   | Regex-based strip |

Default (no Accept header): `text/markdown`

HTML output is wrapped in a minimal template with inline CSS.

#### middleware.py -- Middleware Chain

Decorator-based pipeline. Each middleware wraps the next handler:

```
request --> LogMiddleware --> TimerMiddleware --> ErrorMiddleware --> router.dispatch
response <-- LogMiddleware <-- TimerMiddleware <-- ErrorMiddleware <--
```

| Middleware        | Behavior                                           |
|-------------------|----------------------------------------------------|
| `LogMiddleware`   | Logs `[timestamp] METHOD /path -> STATUS (Xms)`    |
| `TimerMiddleware` | Adds `X-Response-Time` header                      |
| `ErrorMiddleware` | Catches exceptions, returns 500 with `content/500.md` |

#### config.py -- Configuration

Layered configuration with precedence: CLI args > txp.conf > defaults.

```toml
[server]
host = "0.0.0.0"
port = 9000
docroot = "./content"
concurrency = "async"
max_connections = 100

[logging]
level = "info"
format = "structured"
file = "txp.log"

[rendering]
default_format = "text/markdown"
html_template = "template.html"
```

### 3.3 Client (`client/`)

| Module          | Responsibility                              |
|-----------------|---------------------------------------------|
| `connection.py` | TCP connection, send/receive TXP messages   |
| `parser.py`     | Parse raw response bytes into `TxpResponse` |
| `tui.py`        | Curses-based terminal UI                    |
| `history.py`    | Back/forward navigation stack               |
| `bookmarks.py`  | Bookmark persistence (`~/.txp/bookmarks.json`) |

**TUI Layout:**

```
+--------------------------------------------------+
| txp://localhost:9000/index.md          [Address]  |
+--------------------------------------------------+
|                                                   |
|  # TXP Server                                     |
|                                                   |
|  Welcome to the TXP text server.                  |
|                                                   |
|  ## Navigation                                    |
|                                                   |
|  > [About this server](/about.md)      [Link]     |
|    [Useful links](/links.md)                      |
|                                                   |
+--------------------------------------------------+
| 200 OK | text/markdown | 12ms          [Status]   |
+--------------------------------------------------+
```

**Keyboard controls:**

| Key          | Action                   |
|--------------|--------------------------|
| Enter        | Follow selected link     |
| Tab/Shift-Tab| Cycle between links      |
| Backspace    | Navigate back            |
| `g`          | Enter URL manually       |
| `b`          | Show bookmarks           |
| `B`          | Bookmark current page    |
| `q`          | Quit                     |

**URL scheme:** `txp://host:port/path`

---

## 4. Data Flow

### 4.1 GET Request Lifecycle

```
Client                    Server
  |                         |
  |-- GET /about.md ------->|
  |                         |-- parser.py: parse bytes -> TxpRequest
  |                         |-- middleware chain: log, time, error-catch
  |                         |-- router.py: match GET /about.md -> static_handler
  |                         |-- static.py: resolve path, read file
  |                         |-- renderer.py: negotiate format, transform
  |                         |-- response.py: build TxpResponse -> bytes
  |                         |-- middleware chain: add headers, log result
  |<-- 200 OK --------------|
  |                         |
```

### 4.2 POST Form Lifecycle

```
Client                    Server
  |                         |
  |-- POST /guestbook ----->|
  |   name=X&message=Y     |-- parser.py: parse request + body
  |                         |-- router.py: match POST /guestbook -> guestbook_handler
  |                         |-- handler: parse body, append to guestbook.json
  |                         |-- response.py: build 301 Moved -> /guestbook
  |<-- 301 Moved -----------|
  |                         |
  |-- GET /guestbook ------>|
  |<-- 200 OK (entries) ----|
```

---

## 5. Security Architecture

| Threat                | Mitigation                                         |
|-----------------------|----------------------------------------------------|
| Path traversal        | Canonicalize path, reject outside docroot           |
| Request flooding      | `max_connections` limit, 30s idle timeout           |
| Oversized requests    | 8KB header limit, 1MB body limit                   |
| Directory enumeration | No directory listing; 403 for bare directories     |
| Unhandled exceptions  | ErrorMiddleware catches all, returns 500            |

---

## 6. Dependency Map

```
                protocol/
               /    |    \
              /     |     \
         server/  client/  (shared data types)
            |
     +------+------+------+
     |      |      |      |
  listener  router  static  middleware
     |        |       |
  connection  |    renderer
     |        |
   parser   response
```

### External Dependencies

| Dependency | Purpose               | Phase Introduced |
|------------|-----------------------|------------------|
| (stdlib)   | socket, signal, select, asyncio, curses, argparse, json | 0+ |
| `mistune` or `markdown` | Markdown -> HTML rendering | 3 |

---

## 7. File Structure

```
txp/
  server/
    __init__.py
    listener.py        # TCP listener, accept loop (Phase 0, 7)
    connection.py      # Per-connection handler (Phase 0, 2)
    parser.py          # Request parser (Phase 1)
    response.py        # Response builder (Phase 1)
    router.py          # URL -> handler mapping (Phase 4)
    static.py          # File serving from docroot (Phase 2)
    renderer.py        # Markdown -> HTML/plain (Phase 3)
    middleware.py       # Logging, error handling chain (Phase 6)
    config.py          # Server configuration (Phase 2, 9)
  protocol/
    __init__.py
    request.py         # TxpRequest dataclass (Phase 1)
    response.py        # TxpResponse dataclass (Phase 1)
    status.py          # Status codes enum (Phase 1)
    headers.py         # Header parsing/serialization (Phase 1)
  client/
    __init__.py
    connection.py      # TCP client connection (Phase 8)
    parser.py          # Response parser (Phase 8)
    tui.py             # Terminal UI (curses) (Phase 8)
    history.py         # Navigation history (Phase 8)
    bookmarks.py       # Saved pages (Phase 8)
  content/
    index.md           # Root page (Phase 2)
    about.md           # Example pages (Phase 2)
    links.md           # Example pages (Phase 2)
    404.md             # Custom error page (Phase 2)
    500.md             # Custom error page (Phase 6)
  tests/
    test_parser.py     # Phase 1
    test_router.py     # Phase 4
    test_renderer.py   # Phase 3
    test_protocol.py   # Phase 1
    test_integration.py # Phase 9
  txp_server.py        # Entry point: server (Phase 0)
  txp_client.py        # Entry point: client (Phase 8)
  txp.conf             # Configuration file (Phase 9)
```
