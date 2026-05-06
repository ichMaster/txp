# Phase 1 — Issues

## Issues Summary Table

| # | ID | Title | Size | Stage | Dependencies |
|---|---|---|---|---|---|
| 1 | TXP-005 | Protocol data models and status codes | S | 1 — Data Models | TXP-004 |
| 2 | TXP-006 | Header parsing and serialization | S | 1 — Data Models | TXP-005 |
| 3 | TXP-007 | Request parser | S | 2 — Parsing | TXP-005, TXP-006 |
| 4 | TXP-008 | Response builder | S | 3 — Serialization | TXP-005, TXP-006 |
| 5 | TXP-009 | Protocol layer unit tests | S | 4 — Testing | TXP-007, TXP-008 |

**Size legend:** S = 1–2 days, M = 3–5 days, L = 5–8 days

---

## Dependency Tree

```
    TXP-004 (Phase 0 complete)
        |
    TXP-005 (data models + status)
        |
    TXP-006 (headers)
        |
    +---+---+
    v       v
TXP-007  TXP-008
(parser) (builder)
    |       |
    +---+---+
        v
    TXP-009
    (tests)
```

**Parallelization hints:**

- TXP-007 and TXP-008 can run in parallel after TXP-006
- TXP-009 requires both TXP-007 and TXP-008 to be complete

---

## Stage 1 — Data Models

### TXP-005 — Protocol data models and status codes

**Description:**
Define the core data structures for the TXP/1.0 protocol: `TxpRequest`, `TxpResponse` dataclasses, and the `StatusCode` enum. These types are shared between server and client and have no I/O dependencies. They form the foundation that every other module in the project depends on.

**What needs to be done:**
- Create `protocol/` package with `__init__.py`
- In `protocol/status.py`, define `StatusCode` enum with values:
  - `200` — OK (request fulfilled)
  - `301` — Moved (permanent redirect)
  - `400` — Bad Request (parsing error)
  - `403` — Forbidden (access denied)
  - `404` — Not Found (resource not found)
  - `500` — Server Error (internal server error)
- Each enum member must expose `.code` (int) and `.text` (str) attributes
- In `protocol/request.py`, define `TxpRequest` dataclass:
  - `method: str` — one of `GET`, `POST`, `HEAD`, `INFO`
  - `path: str` — URL path (e.g., `/index.md`)
  - `version: str` — protocol version (e.g., `1.0`)
  - `headers: dict[str, str]` — parsed headers
  - `body: str | None` — optional request body (used by POST)
- In `protocol/response.py`, define `TxpResponse` dataclass:
  - `status_code: int` — numeric status code
  - `status_text: str` — human-readable status text
  - `headers: dict[str, str]` — response headers
  - `body: str` — response body (empty string for HEAD)
- Export all public types from `protocol/__init__.py`

**Dependencies:** TXP-004 (Phase 0 complete — `server/` and `protocol/` packages exist)

**Expected result:**
A self-contained `protocol/` package with typed data models that can be imported and used by parser, builder, server, and client modules.

**Acceptance criteria:**
- [ ] `from protocol import TxpRequest, TxpResponse, StatusCode` works
- [ ] `StatusCode` enum has all 6 status codes with correct `.code` and `.text`
- [ ] `TxpRequest` can be instantiated with all fields and optional body
- [ ] `TxpResponse` can be instantiated with all fields
- [ ] Method validation: `TxpRequest` only accepts `GET`, `POST`, `HEAD`, `INFO`
- [ ] All types have proper `__repr__` for debugging

---

### TXP-006 — Header parsing and serialization

**Description:**
Implement header parsing (raw text to dict) and serialization (dict to wire format) as reusable utilities. Headers follow the `Key: Value\r\n` convention, and the parser must handle edge cases like whitespace trimming, empty values, and case-insensitive key matching.

**What needs to be done:**
- In `protocol/headers.py`, implement `parse_headers(raw: str) -> dict[str, str]`:
  - Split on `\r\n`, each line is `Key: Value`
  - Strip leading/trailing whitespace from both key and value
  - Handle missing value (e.g., `Host:\r\n`) -> empty string
  - Case-insensitive key storage (normalize to title case: `content-type` -> `Content-Type`)
  - Stop parsing at empty line (`\r\n\r\n` marks end of headers)
- Implement `serialize_headers(headers: dict[str, str]) -> str`:
  - Produce `Key: Value\r\n` for each entry
  - Deterministic ordering (sorted by key)
  - Return result without trailing `\r\n\r\n` (caller adds separator)
- Handle standard request headers: `Host`, `Accept`, `Content-Type`, `Content-Length`, `User-Agent`
- Handle standard response headers: `Content-Type`, `Content-Length`, `Server`, `Location`, `Date`

**Dependencies:** TXP-005

**Expected result:**
A pair of functions that can round-trip headers between dict and wire format without data loss.

**Acceptance criteria:**
- [ ] `parse_headers("Host: localhost\r\nAccept: text/html\r\n")` returns `{'Host': 'localhost', 'Accept': 'text/html'}`
- [ ] `serialize_headers({'Host': 'localhost'})` returns `"Host: localhost\r\n"`
- [ ] Case normalization: `content-type` input -> `Content-Type` key
- [ ] Whitespace trimming: `"  Host :  localhost  \r\n"` -> `{'Host': 'localhost'}`
- [ ] Empty value handling: `"Host:\r\n"` -> `{'Host': ''}`
- [ ] Round-trip: `parse_headers(serialize_headers(d)) == normalized(d)` for any valid dict

---

## Stage 2 — Parsing

### TXP-007 — Request parser

**Description:**
Implement the request parser that converts raw bytes received from a TCP socket into a structured `TxpRequest` object. The parser must handle the full TXP/1.0 request format: request line, headers, and optional body. Malformed input must be detected and result in a 400 Bad Request response.

**What needs to be done:**
- In `server/parser.py`, implement `parse_request(raw: bytes) -> TxpRequest`:
  - Decode bytes to string (UTF-8)
  - Parse request line: `METHOD /path TXP/1.0\r\n`
    - Extract method, path, and version
    - Validate method is one of: `GET`, `POST`, `HEAD`, `INFO`
    - Validate version format: `TXP/X.Y` where X and Y are digits
  - Parse headers using `protocol.headers.parse_headers()`
  - Parse body:
    - If `Content-Length` header present, read exactly that many bytes as body
    - If no `Content-Length`, body is `None`
  - Return constructed `TxpRequest`
- Implement `parse_request_line(line: str) -> tuple[str, str, str]`:
  - Split request line into method, path, version
  - Raise `ValueError` on malformed line
- Error handling — return `TxpResponse(400, "Bad Request")` for:
  - Empty input
  - Missing or malformed request line
  - Unknown method
  - Missing `\r\n\r\n` header terminator
  - Invalid version string
  - `Content-Length` present but body shorter than declared
- Create `server/__init__.py` if not already present

**Dependencies:** TXP-005, TXP-006

**Expected result:**
Any well-formed TXP/1.0 request can be parsed into a `TxpRequest`. Any malformed input produces a clear 400 error.

**Acceptance criteria:**
- [ ] Valid GET: `"GET /index.md TXP/1.0\r\nHost: localhost\r\n\r\n"` -> `TxpRequest(method='GET', path='/index.md', version='1.0', headers={'Host': 'localhost'}, body=None)`
- [ ] Valid POST with body: `"POST /guestbook TXP/1.0\r\nContent-Length: 5\r\n\r\nhello"` -> body is `"hello"`
- [ ] HEAD request: parsed same as GET but response handler returns no body
- [ ] INFO request: parsed as valid method
- [ ] Empty input -> 400 Bad Request
- [ ] Malformed request line (e.g., `"GET\r\n"`) -> 400 Bad Request
- [ ] Unknown method (e.g., `"DELETE / TXP/1.0"`) -> 400 Bad Request
- [ ] Invalid version (e.g., `"GET / HTTP/1.1"`) -> 400 Bad Request
- [ ] Content-Length mismatch (declared 100, got 5) -> 400 Bad Request

---

## Stage 3 — Serialization

### TXP-008 — Response builder

**Description:**
Implement the response builder that converts a `TxpResponse` object into raw bytes ready to send over a TCP socket. The builder must produce a valid TXP/1.0 response with proper formatting, automatic header injection, and correct `Content-Length` calculation.

**What needs to be done:**
- In `server/response.py`, implement `build_response(response: TxpResponse) -> bytes`:
  - Build status line: `TXP/1.0 {code} {text}\r\n`
  - Auto-set `Content-Length` header from body length (in bytes, not characters)
  - Auto-set `Date` header to current time in ISO 8601 format
  - Auto-set `Server` header to `TXP/1.0`
  - Serialize headers using `protocol.headers.serialize_headers()`
  - Append `\r\n` separator between headers and body
  - Append body (encode to UTF-8)
  - Return complete response as bytes
- Implement convenience factory functions:
  - `ok(body: str, content_type: str = "text/markdown", extra_headers: dict | None = None) -> TxpResponse` — builds 200 OK response
  - `not_found(body: str = "") -> TxpResponse` — builds 404 Not Found
  - `bad_request(body: str = "") -> TxpResponse` — builds 400 Bad Request
  - `redirect(location: str) -> TxpResponse` — builds 301 Moved with Location header
  - `server_error(body: str = "") -> TxpResponse` — builds 500 Server Error
  - `forbidden(body: str = "") -> TxpResponse` — builds 403 Forbidden
- Ensure body encoding handles multibyte UTF-8 characters correctly (Content-Length = byte count, not char count)

**Dependencies:** TXP-005, TXP-006

**Expected result:**
Any `TxpResponse` object can be serialized into valid wire-format bytes. Factory functions simplify building common responses.

**Acceptance criteria:**
- [ ] `build_response(TxpResponse(200, "OK", {}, "Hello"))` produces `b"TXP/1.0 200 OK\r\nContent-Length: 5\r\nDate: ...\r\nServer: TXP/1.0\r\n\r\nHello"`
- [ ] `Content-Length` is computed in bytes: body `"Привет"` (6 chars, 12 bytes) -> `Content-Length: 12`
- [ ] `Date` header present and valid ISO 8601
- [ ] `Server` header present
- [ ] Explicit headers in `TxpResponse` are not overwritten by auto-set (user wins)
- [ ] `ok("# Hello")` builds a 200 response with `Content-Type: text/markdown`
- [ ] `redirect("/about.md")` builds a 301 with `Location: /about.md` and empty body
- [ ] `not_found()`, `bad_request()`, `server_error()`, `forbidden()` build correct status codes
- [ ] Output is valid bytes decodable back to string for text content

---

## Stage 4 — Testing

### TXP-009 — Protocol layer unit tests

**Description:**
Write comprehensive unit tests covering all protocol layer components: data models, header parsing/serialization, request parser, and response builder. Tests must cover valid inputs, edge cases, and all error conditions.

**What needs to be done:**

**`tests/test_protocol.py` — data model and header tests:**
- Test `StatusCode` enum: all 6 codes have correct `.code` and `.text`
- Test `TxpRequest` construction with all field combinations
- Test `TxpResponse` construction with all field combinations
- Test `parse_headers()`: valid headers, empty value, whitespace, case normalization
- Test `serialize_headers()`: deterministic order, correct formatting
- Test round-trip: `parse(serialize(headers)) == normalized(headers)`

**`tests/test_parser.py` — request parser tests:**
- Test valid GET request with path and headers
- Test valid POST request with Content-Length and body
- Test HEAD request (parsed same as GET)
- Test INFO request (valid method)
- Test multiple headers parsed correctly
- Test error: empty input -> 400
- Test error: malformed request line -> 400
- Test error: unknown method -> 400
- Test error: invalid version string -> 400
- Test error: missing header terminator -> 400
- Test error: Content-Length mismatch -> 400

**`tests/test_response.py` — response builder tests:**
- Test `build_response()` produces valid wire format
- Test auto-set headers: Content-Length, Date, Server
- Test Content-Length byte accuracy for multibyte characters
- Test explicit headers not overwritten
- Test factory: `ok()` builds 200 with content-type
- Test factory: `not_found()` builds 404
- Test factory: `bad_request()` builds 400
- Test factory: `redirect()` builds 301 with Location
- Test factory: `server_error()` builds 500
- Test factory: `forbidden()` builds 403

**`tests/` setup:**
- Create `tests/__init__.py`
- Create `tests/conftest.py` with shared fixtures (sample requests, responses)

**Dependencies:** TXP-007, TXP-008

**Expected result:**
A complete test suite that validates every component of the protocol layer. All tests pass with `pytest`.

**Acceptance criteria:**
- [ ] `pytest tests/test_protocol.py` passes — all data model and header tests green
- [ ] `pytest tests/test_parser.py` passes — all parser tests including error cases green
- [ ] `pytest tests/test_response.py` passes — all builder tests including factories green
- [ ] Round-trip test: parse raw bytes -> TxpRequest -> build response -> valid bytes
- [ ] Edge cases covered: empty body, multibyte characters, maximum header count
- [ ] `pytest` runs clean with no warnings

---

## Phase 1 scope notes

**Total effort:** ~3–5 days for a single developer.

**Critical path:** TXP-005 → TXP-006 → TXP-007 / TXP-008 → TXP-009

**Parallel tracks:**
- Track A (parser): TXP-007 — can proceed after TXP-006
- Track B (builder): TXP-008 — can proceed after TXP-006 in parallel with TXP-007

**Prerequisite:** Phase 0 (TCP Echo) must be complete. Phase 1 outputs are integrated into the connection handler from Phase 0 to replace the echo behavior.

**Companion documents:**
- `phase-1-tasks.md` — detailed task tables per stage
- `ARCHITECTURE.md` — protocol layer component architecture
- `ROADMAP.md` — full phase overview and dependency timeline
- `TXP-Server-Specification-EN.md` — protocol format and field definitions
