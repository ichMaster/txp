# TXP/1.0 -- Text Transfer Protocol

## Educational Text Server: Phased Implementation Specification

**Version:** 1.0
**Author:** Vitalii Bondarenko
**Status:** Draft
**Language:** Python 3.11+
**Page Format:** Markdown (.md)

---

## 1. Project Vision

Build a working text server from scratch with a custom protocol TXP (Text Transfer Protocol) that serves Markdown pages. Each phase adds one architectural layer while keeping the system functional at every step.

End result: a fully functional server + TUI client capable of page navigation, Markdown rendering, form processing, and basic routing.

---

## 2. TXP/1.0 Protocol

### 2.1 Request Format

```
METHOD /path TXP/1.0\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

Methods: `GET`, `POST`, `HEAD`, `INFO`

### 2.2 Response Format

```
TXP/1.0 STATUS_CODE STATUS_TEXT\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

### 2.3 Status Codes

| Code | Text          | Description                       |
|------|---------------|-----------------------------------|
| 200  | OK            | Request fulfilled                  |
| 301  | Moved         | Permanent redirect                 |
| 400  | Bad Request   | Request parsing error              |
| 403  | Forbidden     | Access denied                      |
| 404  | Not Found     | Resource not found                 |
| 500  | Server Error  | Internal server error              |

### 2.4 Standard Headers

**Request:**

| Header         | Purpose                            |
|----------------|------------------------------------|
| Host           | Hostname                           |
| Accept         | Desired format: text/markdown, text/html, text/plain |
| Content-Type   | Request body type (for POST)       |
| Content-Length  | Body length in bytes               |
| User-Agent     | Client identifier                  |

**Response:**

| Header         | Purpose                            |
|----------------|------------------------------------|
| Content-Type   | Response content type              |
| Content-Length  | Body length in bytes               |
| Server         | Server identifier                  |
| Location       | Redirect URL (301)                 |
| Date           | Response time (ISO 8601)           |

### 2.5 Content Negotiation

Client specifies `Accept`, server chooses format:

- `text/markdown` -- raw Markdown (client renders)
- `text/html` -- server renders MD -> HTML
- `text/plain` -- Markdown with stripped markup

If Accept is absent, server returns `text/markdown`.

---

## 3. Project Structure (target)

```
txp/
  server/
    __init__.py
    listener.py        # TCP listener, accept loop
    connection.py      # Per-connection handler
    parser.py          # Request parser
    response.py        # Response builder
    router.py          # URL -> handler mapping
    static.py          # File serving from docroot
    renderer.py        # Markdown -> HTML/plain
    middleware.py       # Logging, error handling chain
    config.py          # Server configuration
  protocol/
    __init__.py
    request.py         # TxpRequest dataclass
    response.py        # TxpResponse dataclass
    status.py          # Status codes enum
    headers.py         # Header parsing/serialization
  client/
    __init__.py
    connection.py      # TCP client connection
    parser.py          # Response parser
    tui.py             # Terminal UI (curses)
    history.py         # Navigation history (back/forward)
    bookmarks.py       # Saved pages
  content/
    index.md           # Root page
    about.md           # Example pages
    links.md
    404.md             # Custom error pages
    500.md
  tests/
    test_parser.py
    test_router.py
    test_renderer.py
    test_protocol.py
    test_integration.py
  txp_server.py        # Entry point: server
  txp_client.py        # Entry point: client
  txp.conf             # Configuration file
```

---

## 4. Implementation Phases

---

### Phase 0: TCP Echo (Foundation)

**Goal:** Verify that TCP connectivity works end-to-end.

**Scope:**

- `server/listener.py` -- bind, listen, accept on a given port
- Accept connection, read data, send it back as-is (echo)
- Client -- `telnet localhost 9000` or `nc`

**Deliverables:**

- [ ] TCP listener on configurable port (default 9000)
- [ ] Accept loop with graceful shutdown (SIGINT)
- [ ] Echo: read -> write back -> close
- [ ] Connection logging to stdout

**Acceptance criteria:**

```bash
echo "Hello TXP" | nc localhost 9000
# Output: Hello TXP
```

**Dependencies:** stdlib only (`socket`, `signal`)

**LOE:** 30-50 lines

---

### Phase 1: Protocol Layer

**Goal:** Parse a TXP/1.0 text request and build a structured response.

**Scope:**

- `protocol/request.py` -- dataclass TxpRequest (method, path, version, headers, body)
- `protocol/response.py` -- dataclass TxpResponse (status_code, status_text, headers, body)
- `protocol/status.py` -- enum StatusCode
- `protocol/headers.py` -- parse_headers(), serialize_headers()
- `server/parser.py` -- parse raw bytes -> TxpRequest
- `server/response.py` -- TxpResponse -> raw bytes

**Deliverables:**

- [ ] TxpRequest: method, path, version, headers dict, body (optional)
- [ ] TxpResponse: status_code, status_text, headers dict, body
- [ ] Parser: first line parsing + headers + body
- [ ] Serializer: TxpResponse -> bytes with proper \r\n
- [ ] StatusCode enum: 200, 301, 400, 403, 404, 500
- [ ] Unit tests for parser (valid request, malformed, missing headers)

**Acceptance criteria:**

```
Input:  "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n"
Output: TxpRequest(method='GET', path='/index.md', version='1.0',
                   headers={'Host': 'localhost'}, body=None)
```

**Error handling:** Malformed request -> TxpResponse(400, "Bad Request")

**LOE:** ~120 lines + tests

---

### Phase 2: Static File Server

**Goal:** GET /path.md -> read file from docroot -> TXP response with content.

**Scope:**

- `server/static.py` -- resolve path, read file, build response
- `server/config.py` -- docroot path, port, host
- `content/` -- set of test .md files
- Integration of parser + static + response builder into connection handler

**Deliverables:**

- [ ] Config: docroot, host, port (from file or CLI args)
- [ ] Path resolution: URL path -> filesystem path (within docroot)
- [ ] Security: path traversal protection (../ rejection)
- [ ] GET -> read file -> 200 with Content-Type: text/markdown
- [ ] GET for non-existent file -> 404 with content/404.md
- [ ] HEAD -> same as GET but without body
- [ ] Default document: GET / -> GET /index.md
- [ ] Content-Length header

**Content files:**

```markdown
<!-- content/index.md -->
# TXP Server

Welcome to the TXP text server.

## Navigation

- [About this server](/about.md)
- [Useful links](/links.md)
```

**Acceptance criteria:**

```bash
echo -e "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n" | nc localhost 9000
# TXP/1.0 200 OK
# Content-Type: text/markdown
# Content-Length: ...
#
# # TXP Server
# ...
```

**LOE:** ~150 lines + content

---

### Phase 3: Content Negotiation & Rendering

**Goal:** Server delivers content in the format requested by the client.

**Scope:**

- `server/renderer.py` -- md -> html, md -> plain text
- Accept header parsing and negotiation logic
- Renderer integration into static handler

**Deliverables:**

- [ ] Markdown -> HTML renderer (`markdown` or `mistune` library)
- [ ] Markdown -> Plain text renderer (strip markup)
- [ ] Accept header parser with priorities
- [ ] Response Content-Type matches selected format
- [ ] Fallback: no Accept -> text/markdown

**Rendering pipeline:**

```
Client: Accept: text/html
Server: read .md -> markdown.convert() -> wrap in <html> -> respond
```

Minimal HTML template:

```html
<!DOCTYPE html>
<html>
<head><title>{title}</title>
<style>
  body { font-family: serif; max-width: 720px; margin: 2em auto; }
  code { background: #f0f0f0; padding: 2px 6px; }
  pre  { background: #f0f0f0; padding: 1em; overflow-x: auto; }
  a    { color: #0645ad; }
</style>
</head>
<body>{content}</body>
</html>
```

**Acceptance criteria:**

```bash
# Request HTML
echo -e "GET /index.md TXP/1.0\r\nAccept: text/html\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/html, body = rendered HTML

# Request plain text
echo -e "GET /index.md TXP/1.0\r\nAccept: text/plain\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/plain, body = stripped text
```

**Dependencies:** `mistune` or `markdown` (pip)

**LOE:** ~100 lines

---

### Phase 4: Router & Custom Handlers

**Goal:** Route requests not only to files but also to Python functions.

**Scope:**

- `server/router.py` -- URL pattern matching, handler registry
- INFO method -- returns server metadata
- Dynamic handlers alongside static serving

**Deliverables:**

- [ ] Router: register(method, pattern, handler_fn)
- [ ] Pattern matching: exact paths + simple wildcards (/docs/*)
- [ ] Handler signature: (request: TxpRequest) -> TxpResponse
- [ ] Built-in routes:
  - `INFO /` -> server info (name, version, uptime, page count)
  - `GET /sitemap` -> dynamic list of all .md files from docroot
  - `GET /*.md` -> static file handler (fallback)
- [ ] 405 Method Not Allowed for mismatched methods

**Router API:**

```python
router = Router()
router.add("GET", "/sitemap", sitemap_handler)
router.add("INFO", "/", server_info_handler)
router.add("GET", "/*", static_handler)  # catch-all, lowest priority

handler = router.resolve("GET", "/sitemap")
response = handler(request)
```

**LOE:** ~100 lines

---

### Phase 5: POST & Form Processing

**Goal:** Handle POST requests with text forms.

**Scope:**

- POST body parsing (key=value pairs, url-encoded)
- Form-action pattern in Markdown (custom convention)
- Guestbook as demo application

**Deliverables:**

- [ ] Body parser: `key=value&key2=value2` -> dict
- [ ] POST handler framework
- [ ] Guestbook:
  - `GET /guestbook` -> show entries + form
  - `POST /guestbook` -> add entry, redirect 301 -> GET /guestbook
- [ ] State persistence to file (guestbook.json)
- [ ] Form syntax in Markdown (convention):

```markdown
---form action=/guestbook method=POST
Name: [name]
Message: [message]
[submit:Sign]
---
```

**State management:**

```python
# guestbook.json
[
  {"name": "Vitalii", "message": "First post!", "date": "2026-05-07T10:00:00"}
]
```

**LOE:** ~150 lines

---

### Phase 6: Middleware Chain

**Goal:** Logging, error handling, timing as composable middleware.

**Scope:**

- `server/middleware.py` -- middleware chain pattern
- Three built-in middlewares: logger, error_catcher, timer

**Deliverables:**

- [ ] Middleware signature: (handler) -> handler (decorator pattern)
- [ ] LogMiddleware: logs method, path, status, time
- [ ] ErrorMiddleware: try/except -> 500 response with content/500.md
- [ ] TimerMiddleware: adds X-Response-Time header (ms)
- [ ] Configurable chain order
- [ ] Access log format:

```
[2026-05-07 14:23:01] GET /index.md -> 200 (12ms)
[2026-05-07 14:23:05] GET /missing.md -> 404 (3ms)
```

**Chain composition:**

```python
app = LogMiddleware(TimerMiddleware(ErrorMiddleware(router.dispatch)))
```

**LOE:** ~80 lines

---

### Phase 7: Concurrency

**Goal:** Serve multiple clients simultaneously.

**Scope:**

- Three sequential implementations for comparison:
  1. threading (ThreadPoolExecutor)
  2. select/poll (manual event loop)
  3. asyncio (async/await)

**Deliverables:**

- [ ] ThreadedListener: accept -> submit to thread pool
- [ ] SelectListener: non-blocking sockets + select loop
- [ ] AsyncListener: asyncio.start_server, async handlers
- [ ] Config option: concurrency_model = threaded | select | async
- [ ] Benchmark script: N concurrent requests, measure throughput
- [ ] Connection limit (max_connections in config)

**Benchmark target:**

```bash
python bench.py --connections 50 --requests 200
# threaded:  ~180 req/s
# select:    ~220 req/s
# async:     ~250 req/s
```

**LOE:** ~200 lines (three implementations)

---

### Phase 8: TUI Client

**Goal:** Full-featured terminal client with navigation.

**Scope:**

- `client/` -- TCP client + curses-based TUI
- Link navigation, history, bookmarks

**Deliverables:**

- [ ] TCP client: connect, send TxpRequest, receive TxpResponse
- [ ] TUI layout (curses):
  - Address bar (top): `txp://localhost:9000/index.md`
  - Content area (center): rendered markdown
  - Status bar (bottom): status code, content-type, response time
  - Link highlighting: Tab/Shift-Tab to cycle between links
- [ ] Navigation:
  - Enter on a link -> GET new page
  - Backspace -> back (history)
  - `g` -> enter URL manually
  - `b` -> bookmarks list
  - `B` -> bookmark current page
  - `q` -> quit
- [ ] History stack (back/forward)
- [ ] Bookmarks: saved to ~/.txp/bookmarks.json
- [ ] Markdown rendering in terminal:
  - `#` headings -> bold + color
  - `**bold**` -> bold
  - `*italic*` -> dim/underline
  - `` `code` `` -> reverse video
  - `[text](url)` -> highlighted, navigable
  - Lists -> preserved as-is

**URL scheme:**

```
txp://host:port/path
txp://localhost:9000/about.md
```

**Dependencies:** `curses` (stdlib)

**LOE:** ~350 lines

---

### Phase 9: Configuration & Polish

**Goal:** Production-ready configuration, graceful shutdown, signals.

**Scope:**

- `txp.conf` -- TOML or INI configuration
- CLI arguments (argparse) with config file override
- Graceful shutdown
- PID file
- Structured logging

**Deliverables:**

- [ ] txp.conf parser:

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

- [ ] CLI: `python txp_server.py --port 9001 --docroot /path`
- [ ] SIGINT/SIGTERM -> graceful shutdown (finish active connections)
- [ ] SIGHUP -> reload config
- [ ] PID file: /tmp/txp.pid
- [ ] `--daemon` mode (optional)

**LOE:** ~120 lines

---

## 5. Cross-cutting Concerns

### Security (all phases from Phase 2+)

- Path traversal: canonicalize, reject paths outside docroot
- Request size limit: max 8KB headers, max 1MB body
- Connection timeout: 30s idle -> close
- No directory listing (403 for directories without index.md)

### Testing Strategy

| Phase | Test type                        |
|-------|----------------------------------|
| 0     | Manual (nc/telnet)               |
| 1     | Unit: parser, serializer         |
| 2     | Unit + integration: file serving |
| 3     | Unit: renderer, negotiation      |
| 4     | Unit: router matching            |
| 5     | Integration: POST flow           |
| 6     | Unit: middleware chain            |
| 7     | Load: benchmark script           |
| 8     | Manual: TUI walkthrough          |
| 9     | Integration: full stack          |

### Progress Metrics

| Phase | Cumulative LOC | Running system capability          |
|-------|---------------|------------------------------------|
| 0     | ~50           | TCP echo                           |
| 1     | ~170          | Protocol parsing (no serving)      |
| 2     | ~320          | Static MD file server              |
| 3     | ~420          | Multi-format rendering             |
| 4     | ~520          | Dynamic routes + static            |
| 5     | ~670          | Forms + state                      |
| 6     | ~750          | Observable, resilient server       |
| 7     | ~950          | Concurrent server                  |
| 8     | ~1300         | Server + TUI client                |
| 9     | ~1420         | Production-ready configuration     |

---

## 6. Extension Ideas (post Phase 9)

- **TLS:** socket wrapping with ssl.wrap_socket for txps:// scheme
- **Virtual hosts:** multiple docroots via Host header
- **Caching:** ETag/If-None-Match, 304 Not Modified
- **Plugins:** loading handlers from Python modules via config
- **Inter-linking:** automatic backlinks index (which pages link to this one)
- **Search:** full-text search across docroot (whoosh or simple grep)
- **WebSocket-like:** persistent connection for live reload on file changes
- **Compression:** gzip encoding with Accept-Encoding negotiation
