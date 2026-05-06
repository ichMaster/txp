# Phase 1 — Protocol Layer Tasks

## 1. Data Models

### 1.1 Status codes (`protocol/status.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Create `protocol/` package with `__init__.py` | TXP-005 |
| 2 | Define `StatusCode` enum with 6 status codes: 200 OK, 301 Moved, 400 Bad Request, 403 Forbidden, 404 Not Found, 500 Server Error | TXP-005 |
| 3 | Each enum member exposes `.code` (int) and `.text` (str) attributes | TXP-005 |
| 4 | Add `from_code(code: int) -> StatusCode` class method for reverse lookup | TXP-005 |

### 1.2 Request data model (`protocol/request.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Define `TxpRequest` dataclass with fields: `method`, `path`, `version`, `headers`, `body` | TXP-005 |
| 2 | `method: str` — validated against allowed methods: `GET`, `POST`, `HEAD`, `INFO` | TXP-005 |
| 3 | `path: str` — URL path (e.g., `/index.md`) | TXP-005 |
| 4 | `version: str` — protocol version string (e.g., `1.0`) | TXP-005 |
| 5 | `headers: dict[str, str]` — parsed header key-value pairs | TXP-005 |
| 6 | `body: str | None` — optional request body, default `None` | TXP-005 |

### 1.3 Response data model (`protocol/response.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Define `TxpResponse` dataclass with fields: `status_code`, `status_text`, `headers`, `body` | TXP-005 |
| 2 | `status_code: int` — numeric HTTP-like status code | TXP-005 |
| 3 | `status_text: str` — human-readable status text | TXP-005 |
| 4 | `headers: dict[str, str]` — response header key-value pairs | TXP-005 |
| 5 | `body: str` — response body, default empty string | TXP-005 |

### 1.4 Package exports (`protocol/__init__.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Export `TxpRequest`, `TxpResponse`, `StatusCode` from `protocol/__init__.py` | TXP-005 |

---

## 2. Header Parsing

### 2.1 Header parser (`protocol/headers.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `parse_headers(raw: str) -> dict[str, str]` | TXP-006 |
| 2 | Split input on `\r\n`, parse each line as `Key: Value` | TXP-006 |
| 3 | Strip leading/trailing whitespace from key and value | TXP-006 |
| 4 | Handle missing value (e.g., `Host:\r\n`) -> empty string | TXP-006 |
| 5 | Normalize key to title case (`content-type` -> `Content-Type`) | TXP-006 |
| 6 | Stop at empty line (end of headers) | TXP-006 |

### 2.2 Header serializer (`protocol/headers.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `serialize_headers(headers: dict[str, str]) -> str` | TXP-006 |
| 2 | Produce `Key: Value\r\n` for each entry, sorted by key | TXP-006 |
| 3 | Return string without trailing separator (caller adds `\r\n\r\n`) | TXP-006 |

---

## 3. Request Parser

### 3.1 Request line parser (`server/parser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Create `server/` package with `__init__.py` (if not present from Phase 0) | TXP-007 |
| 2 | Implement `parse_request_line(line: str) -> tuple[str, str, str]` — extract method, path, version | TXP-007 |
| 3 | Validate method is one of: `GET`, `POST`, `HEAD`, `INFO` | TXP-007 |
| 4 | Validate version format: `TXP/X.Y` where X and Y are digits | TXP-007 |
| 5 | Raise `ValueError` on malformed request line | TXP-007 |

### 3.2 Full request parser (`server/parser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `parse_request(raw: bytes) -> TxpRequest` | TXP-007 |
| 2 | Decode raw bytes to UTF-8 string | TXP-007 |
| 3 | Split on `\r\n\r\n` to separate headers from body | TXP-007 |
| 4 | Parse first line via `parse_request_line()` | TXP-007 |
| 5 | Parse remaining header lines via `protocol.headers.parse_headers()` | TXP-007 |
| 6 | If `Content-Length` header present, extract body of that length | TXP-007 |
| 7 | If no `Content-Length`, set body to `None` | TXP-007 |
| 8 | Return constructed `TxpRequest` | TXP-007 |

### 3.3 Error handling (`server/parser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Empty input -> return `TxpResponse(400, "Bad Request")` | TXP-007 |
| 2 | Malformed request line -> 400 | TXP-007 |
| 3 | Unknown method -> 400 | TXP-007 |
| 4 | Missing `\r\n\r\n` header terminator -> 400 | TXP-007 |
| 5 | Invalid version string -> 400 | TXP-007 |
| 6 | Content-Length present but body shorter than declared -> 400 | TXP-007 |

---

## 4. Response Builder

### 4.1 Response serializer (`server/response.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Implement `build_response(response: TxpResponse) -> bytes` | TXP-008 |
| 2 | Build status line: `TXP/1.0 {code} {text}\r\n` | TXP-008 |
| 3 | Auto-set `Content-Length` from body byte length (not char count) | TXP-008 |
| 4 | Auto-set `Date` header in ISO 8601 format | TXP-008 |
| 5 | Auto-set `Server` header to `TXP/1.0` | TXP-008 |
| 6 | Do not overwrite headers already set in `TxpResponse` | TXP-008 |
| 7 | Serialize headers via `protocol.headers.serialize_headers()` | TXP-008 |
| 8 | Append `\r\n` separator and UTF-8 encoded body | TXP-008 |
| 9 | Return complete response as bytes | TXP-008 |

### 4.2 Factory functions (`server/response.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | `ok(body, content_type="text/markdown", extra_headers=None) -> TxpResponse` — 200 OK | TXP-008 |
| 2 | `not_found(body="") -> TxpResponse` — 404 Not Found | TXP-008 |
| 3 | `bad_request(body="") -> TxpResponse` — 400 Bad Request | TXP-008 |
| 4 | `redirect(location) -> TxpResponse` — 301 Moved with Location header | TXP-008 |
| 5 | `server_error(body="") -> TxpResponse` — 500 Server Error | TXP-008 |
| 6 | `forbidden(body="") -> TxpResponse` — 403 Forbidden | TXP-008 |

---

## 5. Unit Tests

### 5.1 Test setup

| # | Task | Issue |
|---|------|-------|
| 1 | Create `tests/__init__.py` | TXP-009 |
| 2 | Create `tests/conftest.py` with shared fixtures: sample raw requests, sample `TxpRequest` instances, sample `TxpResponse` instances | TXP-009 |

### 5.2 Protocol data model tests (`tests/test_protocol.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Test `StatusCode` enum: all 6 codes return correct `.code` and `.text` | TXP-009 |
| 2 | Test `StatusCode.from_code()` reverse lookup for valid and invalid codes | TXP-009 |
| 3 | Test `TxpRequest` construction with all fields | TXP-009 |
| 4 | Test `TxpRequest` with optional body (`None` and string) | TXP-009 |
| 5 | Test `TxpResponse` construction with all fields | TXP-009 |
| 6 | Test `parse_headers()` with valid multi-header input | TXP-009 |
| 7 | Test `parse_headers()` with empty value | TXP-009 |
| 8 | Test `parse_headers()` with whitespace trimming | TXP-009 |
| 9 | Test `parse_headers()` case normalization | TXP-009 |
| 10 | Test `serialize_headers()` formatting and sort order | TXP-009 |
| 11 | Test headers round-trip: `parse(serialize(d)) == normalized(d)` | TXP-009 |

### 5.3 Request parser tests (`tests/test_parser.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Test valid GET request with path and single header | TXP-009 |
| 2 | Test valid GET request with multiple headers | TXP-009 |
| 3 | Test valid POST request with Content-Length and body | TXP-009 |
| 4 | Test HEAD request parsed as valid | TXP-009 |
| 5 | Test INFO request parsed as valid | TXP-009 |
| 6 | Test error: empty input -> 400 Bad Request | TXP-009 |
| 7 | Test error: malformed request line (missing path) -> 400 | TXP-009 |
| 8 | Test error: unknown method (`DELETE`) -> 400 | TXP-009 |
| 9 | Test error: invalid version (`HTTP/1.1`) -> 400 | TXP-009 |
| 10 | Test error: missing header terminator -> 400 | TXP-009 |
| 11 | Test error: Content-Length/body mismatch -> 400 | TXP-009 |

### 5.4 Response builder tests (`tests/test_response.py`)

| # | Task | Issue |
|---|------|-------|
| 1 | Test `build_response()` produces valid wire format bytes | TXP-009 |
| 2 | Test auto-set `Content-Length` matches body byte length | TXP-009 |
| 3 | Test `Content-Length` byte accuracy for multibyte UTF-8 (e.g., Cyrillic) | TXP-009 |
| 4 | Test auto-set `Date` header is valid ISO 8601 | TXP-009 |
| 5 | Test auto-set `Server` header is `TXP/1.0` | TXP-009 |
| 6 | Test explicit headers not overwritten by auto-set | TXP-009 |
| 7 | Test `ok()` factory: status 200, Content-Type set | TXP-009 |
| 8 | Test `not_found()` factory: status 404 | TXP-009 |
| 9 | Test `bad_request()` factory: status 400 | TXP-009 |
| 10 | Test `redirect()` factory: status 301, Location header set | TXP-009 |
| 11 | Test `server_error()` factory: status 500 | TXP-009 |
| 12 | Test `forbidden()` factory: status 403 | TXP-009 |
