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
SLEEP_BETWEEN_PAGES_S = 1.5
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


def save(projects: list[dict]) -> Path:
    """Write projects to data/projects_<timestamp>.json. Returns the path."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = data_dir / f"projects_{timestamp}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
    return out_path


def main() -> None:
    config = load_config()
    session = build_session(config)
    projects = fetch_projects(session)
    out_path = save(projects)
    if not projects:
        print("Warning: 0 projects returned", file=sys.stderr)
    print(f"Saved {len(projects)} projects to {out_path}")


if __name__ == "__main__":
    main()
