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
