# parser_job

A one-shot Python scraper for `https://app.techprojectsnow.com/projects`.
Paginates the Inertia-backed endpoint with session-cookie auth and writes the
combined project list to a timestamped JSON file under `data/`.

## Requirements

- Python 3.14 (managed by [`uv`](https://docs.astral.sh/uv/))
- A logged-in browser session on `app.techprojectsnow.com` (to copy cookies from)

## Setup

```bash
# 1. Install dependencies (creates .venv automatically)
uv sync

# 2. Copy the env template
cp .env.example .env

# 3. Fill in the three cookie values (see "Getting cookies" below)
$EDITOR .env
```

### Getting cookies

In a browser logged into `https://app.techprojectsnow.com`:

1. Open DevTools → **Application** → **Cookies** → `https://app.techprojectsnow.com`
2. Copy these three cookie values into `.env`:

| Cookie in browser | Variable in `.env` |
|---|---|
| `remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d` | `COOKIE_REMEMBER` |
| `techprojectsnow_session` | `COOKIE_SESSION` |
| `XSRF-TOKEN` | `XSRF_TOKEN` |

Values may be URL-encoded in DevTools (trailing `%3D`). Decode `%3D` to `=` when
pasting — `.env` should contain the raw token, typically ending in `==`.

## Usage

```bash
uv run python main.py
```

Progress is printed per page:

```
Page 1: +10 (total 10)
Page 2: +10 (total 20)
...
Page 204: +0 (total 2027)
Saved 2027 projects to data/projects_2026-05-29_143022.json
```

Output goes to `data/projects_<YYYY-MM-DD_HHMMSS>.json` — one file per run, never
overwritten. Each file is a JSON array of project objects exactly as returned by
the API.

## Refreshing expired cookies

When the script prints `Auth expired — refresh cookies in .env` and exits with
code 1, repeat the **Getting cookies** step above. Cookies are session-scoped
and rotate periodically.

## Project layout

```
.
├── main.py             # entrypoint: load_config, build_session, fetch_projects, save
├── .env                # local cookies (gitignored)
├── .env.example        # template
├── data/               # output (gitignored, created on first run)
├── docs/superpowers/
│   ├── specs/          # design specs
│   └── plans/          # implementation plans
├── pyproject.toml
└── uv.lock
```

## Notes

- No retry / backoff. Network errors surface as a traceback; auth or shape
  errors print a clear message and exit 1.
- 0.5s sleep between pages to be polite — adjustable via `SLEEP_BETWEEN_PAGES_S`
  in `main.py`.
- Never commit `.env` or `data/` — both are gitignored.
