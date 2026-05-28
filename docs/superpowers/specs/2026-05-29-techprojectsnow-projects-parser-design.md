# techprojectsnow Projects Parser — Design

**Date:** 2026-05-29
**Status:** Approved (pending spec review)

## Goal

Fetch all projects from `https://app.techprojectsnow.com/projects` (an Inertia.js
endpoint behind session auth) and save them as a flat JSON array to a timestamped
file under `data/`.

## Non-goals

- No retry/backoff logic beyond a polite inter-page sleep.
- No tests in v1 — this is a one-shot scraper against a live endpoint.
- No transformation or curation of project fields. Whatever the API returns
  inside `props.projects.data` is what gets saved.
- No automatic cookie refresh / login flow. Cookies are supplied by the user
  via `.env` and refreshed manually when they expire.

## Architecture

Single-file script (`main.py`) with this flow:

```
load .env  →  build requests.Session (cookies + Inertia headers)
   ↓
loop page = 1, 2, 3...
   GET /projects?page={N}&limit=10
   parse JSON → extract props.projects.data
   append to accumulator
   stop when current_page >= last_page  (fallback: stop when data is empty)
   sleep 0.5s between pages
   ↓
write accumulator → data/projects_YYYY-MM-DD_HHMMSS.json
print "Saved N projects to <path>"
```

### Inertia response shape

Because the request sends `X-Inertia: true`, `X-Inertia-Version: ...`, and
`X-Requested-With: XMLHttpRequest`, the server returns JSON of roughly this
shape:

```json
{
  "component": "Projects/Index",
  "props": {
    "projects": {
      "data": [ { ...project... }, ... ],
      "current_page": 1,
      "last_page": 7,
      "per_page": 10,
      "total": 63
    }
  },
  "url": "/projects?page=1&limit=10",
  "version": "7c010bf7dddd0a47041d6d8e9fc03b9e"
}
```

The parser reads `props.projects.data` (the project list) and
`props.projects.last_page` (the stop condition).

## Components (file layout)

```
parser_job/
├── main.py              # entrypoint (~80 lines)
├── .env                 # COOKIE_REMEMBER, COOKIE_SESSION, XSRF_TOKEN (gitignored)
├── .env.example         # template with empty values, committed
├── .gitignore           # add .env and data/
├── data/                # output dir, gitignored, created at runtime
│   └── projects_2026-05-29_143022.json
└── pyproject.toml       # add python-dotenv to dependencies
```

### Functions in `main.py`

- `load_config() -> dict` — reads `.env` via `python-dotenv`, returns a dict
  with `cookies` (dict for `requests`) and `xsrf_token` (string).
- `build_session(config) -> requests.Session` — creates a `Session`, sets the
  cookies and the Inertia/browser headers copied from the curl example
  (`Accept`, `Content-Type`, `X-Inertia`, `X-Inertia-Version`,
  `X-Requested-With`, `X-XSRF-TOKEN`, `User-Agent`, `Referer`).
- `fetch_projects(session) -> list[dict]` — loops pages, appends
  `props.projects.data` to a list, stops at `last_page` (or first empty page),
  sleeps 0.5s between pages. Returns the combined list.
- `save(projects) -> Path` — creates `data/` if missing, writes
  `data/projects_<timestamp>.json` with `indent=2` and `ensure_ascii=False`,
  returns the path.
- `main()` — wires them together and prints
  `Saved {len(projects)} projects to {path}`.

### .env keys

```
COOKIE_REMEMBER=...    # remember_web_59ba36... value
COOKIE_SESSION=...     # techprojectsnow_session value
XSRF_TOKEN=...         # XSRF-TOKEN cookie value (also sent as X-XSRF-TOKEN header)
```

The remember-cookie name (`remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d`)
is hardcoded in `main.py` as a constant — it is derived from the app's auth
guard and does not change per user/session.

## Error handling

| Condition | Behavior |
|---|---|
| `.env` missing or required key empty | Print which key is missing and exit 1 |
| Auth expired — detected as HTTP 401/403, OR a 2xx response whose `Content-Type` is not `application/json` (Inertia redirects unauthenticated requests to an HTML login page) | Print "Auth expired — refresh cookies in .env" and exit 1 |
| Other HTTP error | `response.raise_for_status()` — readable traceback, non-zero exit |
| Unexpected response shape (no `props.projects.data`) | Print first 500 chars of response body and exit 1 |
| Empty result set | Write empty JSON array, print a warning, exit 0 |
| Rate limit observed (429) | Treated as a fatal HTTP error in v1 (no backoff) |

## Output format

A single JSON file containing a flat array of project objects exactly as
returned by the API:

```json
[
  { ...project 1 fields verbatim... },
  { ...project 2 fields verbatim... }
]
```

Written with `json.dump(projects, f, indent=2, ensure_ascii=False)`.

## Dependencies

Add to `pyproject.toml`:

- `python-dotenv` (for `.env` loading) — existing `requests` stays.

## Out of scope (deferred)

- Retries with exponential backoff
- CLI flags for page range / output path
- Resuming partial runs
- Unit tests with a mocked session
- Automatic re-login when cookies expire
