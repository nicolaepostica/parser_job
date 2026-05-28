# techprojectsnow Projects Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-shot Python script that paginates `https://app.techprojectsnow.com/projects`, extracts the Inertia `props.projects.data` array from every page, and writes the combined list to a timestamped JSON file under `data/`.

**Architecture:** Single-file script (`main.py`) using `requests.Session` with session cookies loaded from `.env`. The Inertia headers (`X-Inertia`, `X-Inertia-Version`, `X-Requested-With`) make the endpoint return JSON. Loops `page=1..last_page` (read from the response), sleeps 0.5s between requests, writes one JSON file at the end.

**Tech Stack:** Python 3.14, `requests`, `python-dotenv`, `uv` for dependency management.

**Spec:** `docs/superpowers/specs/2026-05-29-techprojectsnow-projects-parser-design.md`

**Note on testing:** Per the spec ("No tests in v1 — it's a one-shot scraper against a live endpoint"), this plan uses manual verification instead of automated tests. The final task runs the full script end-to-end against the live API to verify everything works together.

---

## File Structure

| Path | Status | Responsibility |
|---|---|---|
| `.gitignore` | modify | Exclude `.env` and `data/` from git |
| `.env.example` | create | Template showing required cookie keys (committed) |
| `.env` | create (local only) | Actual cookie values (gitignored) |
| `pyproject.toml` | modify | Add `python-dotenv` dependency |
| `main.py` | rewrite | Entire parser: load config, paginate, save |
| `data/` | created at runtime | Output directory for timestamped JSON files |

---

## Task 1: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Read current `.gitignore`**

Run: `cat .gitignore`
Expected: existing Python ignores (likely `__pycache__`, `.venv`, etc.).

- [ ] **Step 2: Append `.env` and `data/` to `.gitignore`**

Append these lines to `.gitignore` (only if not already present):

```
# local secrets
.env

# scraper output
data/
```

- [ ] **Step 3: Verify**

Run: `grep -E '^\.env$|^data/$' .gitignore`
Expected: both lines appear in output.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore .env and data/ output"
```

---

## Task 2: Add `python-dotenv` dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock` (automatically)

- [ ] **Step 1: Add the dependency via uv**

Run: `uv add python-dotenv`
Expected: `pyproject.toml` updated; `uv.lock` regenerated; `.venv` gets the package installed.

- [ ] **Step 2: Verify it's in `pyproject.toml`**

Run: `grep python-dotenv pyproject.toml`
Expected: a line like `"python-dotenv>=1.0.0",` inside `dependencies = [...]`.

- [ ] **Step 3: Verify the import works**

Run: `uv run python -c "from dotenv import load_dotenv; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add python-dotenv dependency"
```

---

## Task 3: Create `.env.example`

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create `.env.example` with empty values**

Write this exact content to `.env.example`:

```
# Cookies copied from a logged-in browser session at https://app.techprojectsnow.com
# Open DevTools -> Application -> Cookies -> copy the values listed below.
# These expire periodically; refresh them when the parser prints "Auth expired".

COOKIE_REMEMBER=
COOKIE_SESSION=
XSRF_TOKEN=
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: add .env.example template for parser cookies"
```

---

## Task 4: Create local `.env` from the curl example

**Files:**
- Create: `.env` (gitignored, do NOT commit)

- [ ] **Step 1: Extract cookie values from the curl example in the existing `main.py`**

The current `main.py` contains a curl example in a comment block. From the `-b` cookie header, extract three values:

- `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=...` → `COOKIE_REMEMBER`
- `techprojectsnow_session=...` → `COOKIE_SESSION`
- `XSRF-TOKEN=...` → `XSRF_TOKEN`

URL-decode the trailing `%3D` to `=` in each value (the cookie values end with `==` base64 padding).

- [ ] **Step 2: Write `.env` with the extracted values**

Create `.env` with this shape (filling in the actual values):

```
COOKIE_REMEMBER=eyJpdiI6ImZQNHFWZDlzK2hqUTNTZzd2d25pZGc9PSIsInZhbHVlIjoi...==
COOKIE_SESSION=eyJpdiI6Im10WTVrRGx2OUNINmY5cDJmTEVYc1E9PSIsInZhbHVlIjoi...==
XSRF_TOKEN=eyJpdiI6InRWcU94SjVDUHBCUnhYd0R2VlRiMVE9PSIsInZhbHVlIjoi...==
```

- [ ] **Step 3: Verify `.env` is gitignored**

Run: `git status --short .env`
Expected: empty output (no entry — meaning git is ignoring it).

- [ ] **Step 4: Do NOT commit**

`.env` must not be committed. Skip to the next task.

---

## Task 5: Implement `load_config()` in `main.py`

**Files:**
- Rewrite: `main.py`

- [ ] **Step 1: Replace the entire `main.py` with a stub containing imports, constants, and `load_config()`**

Write this exact content to `main.py` (this replaces the current file, including the curl-comment block — the spec lives in docs now, and the values were extracted to `.env` in Task 4):

```python
"""Parser for https://app.techprojectsnow.com/projects.

Paginates the Inertia-backed projects endpoint and saves the combined list
of projects to a timestamped JSON file under data/.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

BASE_URL = "https://app.techprojectsnow.com"
PROJECTS_PATH = "/projects"
PAGE_LIMIT = 10
SLEEP_BETWEEN_PAGES_S = 0.5
INERTIA_VERSION = "7c010bf7dddd0a47041d6d8e9fc03b9e"
REMEMBER_COOKIE_NAME = "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d"


def load_config() -> dict:
    """Load cookies and XSRF token from .env. Exit 1 if any are missing."""
    load_dotenv()
    required = ["COOKIE_REMEMBER", "COOKIE_SESSION", "XSRF_TOKEN"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"Missing required keys in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return {
        "cookies": {
            REMEMBER_COOKIE_NAME: os.environ["COOKIE_REMEMBER"],
            "techprojectsnow_session": os.environ["COOKIE_SESSION"],
            "XSRF-TOKEN": os.environ["XSRF_TOKEN"],
        },
        "xsrf_token": os.environ["XSRF_TOKEN"],
    }


def main() -> None:
    config = load_config()
    print(f"Loaded {len(config['cookies'])} cookies from .env")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it to verify `load_config()` works against the real `.env`**

Run: `uv run python main.py`
Expected: `Loaded 3 cookies from .env`

- [ ] **Step 3: Verify the missing-key path exits cleanly**

Run: `uv run env -u COOKIE_REMEMBER python -c "import os; os.environ.pop('COOKIE_REMEMBER', None); from main import load_config; load_config()"`

(Easier alternative — temporarily rename `.env`):

```bash
mv .env .env.bak
uv run python main.py; echo "exit=$?"
mv .env.bak .env
```

Expected: prints `Missing required keys in .env: COOKIE_REMEMBER, COOKIE_SESSION, XSRF_TOKEN` and `exit=1`.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: scaffold parser with load_config()"
```

---

## Task 6: Implement `build_session()`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add `build_session()` above `main()`**

Insert this function in `main.py` after `load_config()` and before `main()`:

```python
def build_session(config: dict) -> requests.Session:
    """Build a requests.Session with cookies and Inertia headers."""
    session = requests.Session()
    for name, value in config["cookies"].items():
        session.cookies.set(name, value, domain="app.techprojectsnow.com")
    session.headers.update({
        "Accept": "text/html, application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Referer": f"{BASE_URL}{PROJECTS_PATH}",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "X-Inertia": "true",
        "X-Inertia-Version": INERTIA_VERSION,
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": config["xsrf_token"],
    })
    return session
```

- [ ] **Step 2: Update `main()` to build the session and print a confirmation**

Replace the body of `main()` with:

```python
def main() -> None:
    config = load_config()
    session = build_session(config)
    print(f"Session ready — {len(session.cookies)} cookies, {len(session.headers)} headers")
```

- [ ] **Step 3: Run it**

Run: `uv run python main.py`
Expected: `Session ready — 3 cookies, N headers` (N is around 10-12, depending on requests' defaults).

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: build authenticated requests.Session with Inertia headers"
```

---

## Task 7: Implement `fetch_projects()`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add `fetch_projects()` above `main()`**

Insert this function in `main.py` after `build_session()`:

```python
def fetch_projects(session: requests.Session) -> list[dict]:
    """Paginate /projects and return the combined list of project dicts.

    Stops when current_page >= last_page (Inertia paginator metadata), or
    when a page returns an empty data array as a fallback.
    """
    projects: list[dict] = []
    page = 1
    while True:
        url = f"{BASE_URL}{PROJECTS_PATH}"
        response = session.get(url, params={"page": page, "limit": PAGE_LIMIT})

        if response.status_code in (401, 403):
            print("Auth expired — refresh cookies in .env", file=sys.stderr)
            sys.exit(1)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            print("Auth expired — refresh cookies in .env", file=sys.stderr)
            sys.exit(1)

        payload = response.json()
        try:
            paginator = payload["props"]["projects"]
            page_data = paginator["data"]
        except (KeyError, TypeError):
            print("Unexpected response shape. First 500 chars:", file=sys.stderr)
            print(response.text[:500], file=sys.stderr)
            sys.exit(1)

        projects.extend(page_data)
        last_page = paginator.get("last_page")
        print(f"Page {page}: +{len(page_data)} (total {len(projects)})")

        if not page_data:
            break
        if last_page is not None and page >= last_page:
            break

        page += 1
        time.sleep(SLEEP_BETWEEN_PAGES_S)

    return projects
```

- [ ] **Step 2: Update `main()` to call `fetch_projects()` and print the count**

Replace the body of `main()` with:

```python
def main() -> None:
    config = load_config()
    session = build_session(config)
    projects = fetch_projects(session)
    print(f"Fetched {len(projects)} projects total")
```

- [ ] **Step 3: Run it against the live API**

Run: `uv run python main.py`
Expected: prints one `Page N: +K (total X)` line per page, then `Fetched X projects total`. If you see `Auth expired`, refresh cookies in `.env` and retry.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: paginate projects endpoint and accumulate results"
```

---

## Task 8: Implement `save()` and wire up `main()`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add `save()` above `main()`**

Insert this function in `main.py` after `fetch_projects()`:

```python
def save(projects: list[dict]) -> Path:
    """Write projects to data/projects_<timestamp>.json. Returns the path."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = data_dir / f"projects_{timestamp}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    return out_path
```

- [ ] **Step 2: Update `main()` to save and print the final message**

Replace the body of `main()` with:

```python
def main() -> None:
    config = load_config()
    session = build_session(config)
    projects = fetch_projects(session)
    out_path = save(projects)
    if not projects:
        print("Warning: 0 projects returned", file=sys.stderr)
    print(f"Saved {len(projects)} projects to {out_path}")
```

- [ ] **Step 3: Run the full pipeline against the live API**

Run: `uv run python main.py`
Expected: per-page progress lines, then `Saved X projects to data/projects_YYYY-MM-DD_HHMMSS.json`.

- [ ] **Step 4: Verify the output file**

Run: `ls -la data/ && python -c "import json; d=json.load(open(sorted(__import__('pathlib').Path('data').glob('projects_*.json'))[-1])); print(f'array length: {len(d)}'); print(f'first item keys: {list(d[0].keys()) if d else \"(empty)\"}')"`
Expected: lists the file, prints `array length: X` matching the script's count, and prints the field names of the first project.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat: write fetched projects to timestamped JSON file"
```

---

## Self-Review

**Spec coverage:**
- All pages (paginate until done) → Task 7 (`last_page` + empty-fallback stop)
- Flat list of projects only → Task 7 extracts `props.projects.data`, Task 8 saves it as a flat array
- Auth via `.env` (gitignored) → Tasks 1, 3, 4, 5
- Timestamped file under `data/` → Task 8 (`save()`)
- `python-dotenv` dependency → Task 2
- `.gitignore` for `.env` and `data/` → Task 1
- Error handling: missing .env keys → Task 5; auth expired (401/403 + non-JSON Content-Type) → Task 7; unexpected shape → Task 7; empty result warning → Task 8; HTTP errors via `raise_for_status` → Task 7

**Placeholder scan:** No "TBD", "TODO", or "add appropriate handling" — every step contains the actual code or command.

**Type consistency:** `load_config()` returns `dict` with keys `cookies` and `xsrf_token`; `build_session()` reads exactly those keys. `fetch_projects()` returns `list[dict]`; `save()` accepts `list[dict]` and returns `Path`. Constant names (`BASE_URL`, `PROJECTS_PATH`, `PAGE_LIMIT`, `SLEEP_BETWEEN_PAGES_S`, `INERTIA_VERSION`, `REMEMBER_COOKIE_NAME`) match between definition (Task 5) and use (Tasks 6, 7).
