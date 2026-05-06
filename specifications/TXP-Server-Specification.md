# TXP/1.0 -- Text Transfer Protocol

## Educational Text Server: Phased Implementation Specification

**Version:** 1.0
**Author:** Vitalii Bondarenko
**Status:** Draft
**Language:** Python 3.11+
**Page Format:** Markdown (.md)

---

## 1. Project Vision

Побудувати з нуля працюючий текстовий сервер з власним протоколом TXP (Text Transfer Protocol), який обслуговує Markdown-сторінки. Кожна фаза додає один архітектурний шар, зберігаючи працездатність системи на кожному кроці.

Кінцевий результат: повнофункціональний сервер + TUI-клієнт, здатний обслуговувати навігацію між сторінками, рендерити Markdown, обробляти форми та підтримувати базову маршрутизацію.

---

## 2. Протокол TXP/1.0

### 2.1 Формат запиту

```
METHOD /path TXP/1.0\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

Методи: `GET`, `POST`, `HEAD`, `INFO`

### 2.2 Формат відповіді

```
TXP/1.0 STATUS_CODE STATUS_TEXT\r\n
Header-Name: Header-Value\r\n
\r\n
[body]
```

### 2.3 Коди статусу

| Код | Текст         | Опис                              |
|-----|---------------|-----------------------------------|
| 200 | OK            | Запит виконано                     |
| 301 | Moved         | Постійне перенаправлення           |
| 400 | Bad Request   | Помилка парсингу запиту            |
| 403 | Forbidden     | Доступ заборонено                  |
| 404 | Not Found     | Ресурс не знайдено                 |
| 500 | Server Error  | Внутрішня помилка сервера          |

### 2.4 Стандартні заголовки

**Запит:**

| Заголовок      | Призначення                        |
|----------------|------------------------------------|
| Host           | Ім'я хоста                         |
| Accept         | Бажаний формат: text/markdown, text/html, text/plain |
| Content-Type   | Тип тіла запиту (для POST)         |
| Content-Length | Довжина тіла в байтах              |
| User-Agent     | Ідентифікатор клієнта              |

**Відповідь:**

| Заголовок      | Призначення                        |
|----------------|------------------------------------|
| Content-Type   | Тип контенту відповіді             |
| Content-Length | Довжина тіла в байтах              |
| Server         | Ідентифікатор сервера              |
| Location       | URL для перенаправлення (301)      |
| Date           | Час відповіді (ISO 8601)           |

### 2.5 Content Negotiation

Клієнт вказує `Accept`, сервер обирає формат:

- `text/markdown` -- сирий Markdown (клієнт рендерить сам)
- `text/html` -- сервер рендерить MD -> HTML
- `text/plain` -- Markdown зі stripped-розміткою

Якщо Accept відсутній, сервер віддає `text/markdown`.

---

## 3. Структура проекту (цільова)

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

## 4. Фази реалізації

---

### Phase 0: TCP Echo (Foundation)

**Мета:** Перевірити, що TCP-з'єднання працює end-to-end.

**Scope:**

- `server/listener.py` -- bind, listen, accept на заданому порті
- Прийняти з'єднання, прочитати дані, відправити їх назад як є (echo)
- Клієнт -- `telnet localhost 9000` або `nc`

**Deliverables:**

- [ ] TCP listener на конфігурованому порті (default 9000)
- [ ] Accept loop з graceful shutdown (SIGINT)
- [ ] Echo: read -> write back -> close
- [ ] Логування з'єднань в stdout

**Acceptance criteria:**

```bash
echo "Hello TXP" | nc localhost 9000
# Output: Hello TXP
```

**Dependencies:** тільки stdlib (`socket`, `signal`)

**LOE:** 30-50 рядків

---

### Phase 1: Protocol Layer

**Мета:** Парсити текстовий запит TXP/1.0 і формувати структуровану відповідь.

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
- [ ] Parser: розбір першого рядка + заголовків + тіла
- [ ] Serializer: TxpResponse -> bytes з правильним \r\n
- [ ] StatusCode enum: 200, 301, 400, 403, 404, 500
- [ ] Unit tests для parser (valid request, malformed, missing headers)

**Acceptance criteria:**

```
Input:  "GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n"
Output: TxpRequest(method='GET', path='/index.md', version='1.0',
                   headers={'Host': 'localhost'}, body=None)
```

**Error handling:** Malformed request -> TxpResponse(400, "Bad Request")

**LOE:** ~120 рядків + тести

---

### Phase 2: Static File Server

**Мета:** GET /path.md -> читання файлу з docroot -> TXP-відповідь з вмістом.

**Scope:**

- `server/static.py` -- resolve path, read file, build response
- `server/config.py` -- docroot path, port, host
- `content/` -- набір тестових .md файлів
- Інтеграція parser + static + response builder в connection handler

**Deliverables:**

- [ ] Config: docroot, host, port (з файлу або CLI args)
- [ ] Path resolution: URL path -> filesystem path (всередині docroot)
- [ ] Security: path traversal protection (../ rejection)
- [ ] GET -> read file -> 200 з Content-Type: text/markdown
- [ ] GET неіснуючого файлу -> 404 з content/404.md
- [ ] HEAD -> як GET, але без body
- [ ] Default document: GET / -> GET /index.md
- [ ] Content-Length заголовок

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

**LOE:** ~150 рядків + content

---

### Phase 3: Content Negotiation & Rendering

**Мета:** Сервер віддає контент у форматі, який запитує клієнт.

**Scope:**

- `server/renderer.py` -- md -> html, md -> plain text
- Accept header parsing та negotiation logic
- Підключення рендерера в static handler

**Deliverables:**

- [ ] Markdown -> HTML renderer (бібліотека `markdown` або `mistune`)
- [ ] Markdown -> Plain text renderer (strip markup)
- [ ] Accept header parser з пріоритетами
- [ ] Content-Type відповіді відповідає обраному формату
- [ ] Fallback: без Accept -> text/markdown

**Rendering pipeline:**

```
Client: Accept: text/html
Server: read .md -> markdown.convert() -> wrap in <html> -> respond
```

HTML template (мінімальний):

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
# Запит HTML
echo -e "GET /index.md TXP/1.0\r\nAccept: text/html\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/html, body = rendered HTML

# Запит plain
echo -e "GET /index.md TXP/1.0\r\nAccept: text/plain\r\n\r\n" | nc localhost 9000
# -> Content-Type: text/plain, body = stripped text
```

**Dependencies:** `mistune` або `markdown` (pip)

**LOE:** ~100 рядків

---

### Phase 4: Router & Custom Handlers

**Мета:** Маршрутизація запитів не тільки до файлів, а й до Python-функцій.

**Scope:**

- `server/router.py` -- URL pattern matching, handler registry
- INFO метод -- повертає метадані сервера
- Dynamic handlers поруч зі static serving

**Deliverables:**

- [ ] Router: register(method, pattern, handler_fn)
- [ ] Pattern matching: exact paths + simple wildcards (/docs/*)
- [ ] Handler signature: (request: TxpRequest) -> TxpResponse
- [ ] Built-in routes:
  - `INFO /` -> server info (name, version, uptime, page count)
  - `GET /sitemap` -> динамічний список всіх .md файлів з docroot
  - `GET /*.md` -> static file handler (fallback)
- [ ] 405 Method Not Allowed для невідповідних методів

**Router API:**

```python
router = Router()
router.add("GET", "/sitemap", sitemap_handler)
router.add("INFO", "/", server_info_handler)
router.add("GET", "/*", static_handler)  # catch-all, lowest priority

handler = router.resolve("GET", "/sitemap")
response = handler(request)
```

**LOE:** ~100 рядків

---

### Phase 5: POST & Form Processing

**Мета:** Обробка POST-запитів з текстовими формами.

**Scope:**

- POST body parsing (key=value pairs, url-encoded)
- Form-action pattern в Markdown (custom convention)
- Guestbook як демо-застосунок

**Deliverables:**

- [ ] Body parser: `key=value&key2=value2` -> dict
- [ ] POST handler framework
- [ ] Guestbook:
  - `GET /guestbook` -> показує записи + форму
  - `POST /guestbook` -> додає запис, redirect 301 -> GET /guestbook
- [ ] Збереження стану у файл (guestbook.json)
- [ ] Form syntax в Markdown (convention):

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

**LOE:** ~150 рядків

---

### Phase 6: Middleware Chain

**Мета:** Logging, error handling, timing як composable middleware.

**Scope:**

- `server/middleware.py` -- middleware chain pattern
- Три built-in middleware: logger, error_catcher, timer

**Deliverables:**

- [ ] Middleware signature: (handler) -> handler (decorator pattern)
- [ ] LogMiddleware: логує method, path, status, time
- [ ] ErrorMiddleware: try/except -> 500 response з content/500.md
- [ ] TimerMiddleware: додає X-Response-Time header (ms)
- [ ] Configurable chain order
- [ ] Access log формат:

```
[2026-05-07 14:23:01] GET /index.md -> 200 (12ms)
[2026-05-07 14:23:05] GET /missing.md -> 404 (3ms)
```

**Chain composition:**

```python
app = LogMiddleware(TimerMiddleware(ErrorMiddleware(router.dispatch)))
```

**LOE:** ~80 рядків

---

### Phase 7: Concurrency

**Мета:** Обслуговування декількох клієнтів одночасно.

**Scope:**

- Три послідовні реалізації для порівняння:
  1. threading (ThreadPoolExecutor)
  2. select/poll (event loop вручну)
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

**LOE:** ~200 рядків (три реалізації)

---

### Phase 8: TUI Client

**Мета:** Повноцінний термінальний клієнт з навігацією.

**Scope:**

- `client/` -- TCP клієнт + curses-based TUI
- Навігація по посиланнях, history, bookmarks

**Deliverables:**

- [ ] TCP client: connect, send TxpRequest, receive TxpResponse
- [ ] TUI layout (curses):
  - Address bar (top): `txp://localhost:9000/index.md`
  - Content area (center): rendered markdown
  - Status bar (bottom): status code, content-type, response time
  - Link highlighting: Tab/Shift-Tab для переключення між посиланнями
- [ ] Navigation:
  - Enter на посиланні -> GET нова сторінка
  - Backspace -> назад (history)
  - `g` -> ввести URL вручну
  - `b` -> bookmarks list
  - `B` -> bookmark current page
  - `q` -> quit
- [ ] History stack (back/forward)
- [ ] Bookmarks: збереження у ~/.txp/bookmarks.json
- [ ] Markdown rendering в terminal:
  - `#` заголовки -> bold + color
  - `**bold**` -> bold
  - `*italic*` -> dim/underline
  - `` `code` `` -> reverse video
  - `[text](url)` -> highlighted, navigable
  - Списки -> збережені як є

**URL scheme:**

```
txp://host:port/path
txp://localhost:9000/about.md
```

**Dependencies:** `curses` (stdlib)

**LOE:** ~350 рядків

---

### Phase 9: Configuration & Polish

**Мета:** Production-ready конфігурація, graceful shutdown, сигнали.

**Scope:**

- `txp.conf` -- TOML або INI конфігурація
- CLI arguments (argparse) з override config file
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

**LOE:** ~120 рядків

---

## 5. Cross-cutting concerns

### Security (all phases from Phase 2+)

- Path traversal: canonicalize, reject paths outside docroot
- Request size limit: max 8KB headers, max 1MB body
- Connection timeout: 30s idle -> close
- No directory listing (403 для директорій без index.md)

### Testing strategy

| Phase | Test type                    |
|-------|------------------------------|
| 0     | Manual (nc/telnet)           |
| 1     | Unit: parser, serializer     |
| 2     | Unit + integration: file serving |
| 3     | Unit: renderer, negotiation  |
| 4     | Unit: router matching        |
| 5     | Integration: POST flow       |
| 6     | Unit: middleware chain        |
| 7     | Load: benchmark script       |
| 8     | Manual: TUI walkthrough      |
| 9     | Integration: full stack      |

### Метрики прогресу

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

## 6. Extension ideas (post Phase 9)

- **TLS:** обгортка сокету в ssl.wrap_socket для txps:// scheme
- **Virtual hosts:** декілька docroots за Host header
- **Caching:** ETag/If-None-Match, 304 Not Modified
- **Plugins:** завантаження handler-ів з Python-модулів по конфігу
- **Inter-linking:** автоматичний backlinks index (які сторінки посилаються на цю)
- **Search:** повнотекстовий пошук по docroot (whoosh або просто grep)
- **WebSocket-like:** persistent connection для live reload при зміні файлів
- **Compression:** gzip encoding з Accept-Encoding negotiation
