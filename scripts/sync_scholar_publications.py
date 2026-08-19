#!/usr/bin/env python3
"""Synchronize the public Google Scholar profile into Hugo's data directory.

Google Scholar does not provide an official public profile API. This script reads
the public profile HTML and keeps the last successful JSON snapshot when Scholar
rate-limits automated requests or presents a verification page.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "scholar_publications.json"
PROFILE_ID = os.environ.get("GOOGLE_SCHOLAR_ID", "0O1EN4QAAAAJ")
PROFILE_URL = (
    "https://scholar.google.com/citations"
    f"?user={PROFILE_ID}&hl=en&pagesize=100&view_op=list_works"
)


def text_content(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(html.unescape(fragment).split())


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def sentence_case_title(value: str) -> str:
    """Use sentence case while preserving scientific acronyms and model names."""
    protected = {
        token.casefold(): token
        for token in re.findall(r"\b(?:[A-Z0-9]{2,}|[a-z][A-Z][A-Za-z0-9]*)\b", value)
    }
    protected.update({"fmri": "fMRI", "medslip": "MeDSLIP", "3d": "3D"})
    lowered = value.lower()
    words = re.split(r"(\b)", lowered)
    words = [protected.get(word.casefold(), word) for word in words]
    result = "".join(words)
    return result[:1].upper() + result[1:] if result else result


def parse_profile(page: str) -> list[dict[str, object]]:
    rows = re.findall(
        r'<tr[^>]*class="[^"]*\bgsc_a_tr\b[^"]*"[^>]*>(.*?)</tr>',
        page,
        flags=re.DOTALL | re.IGNORECASE,
    )
    publications: list[dict[str, object]] = []

    for row in rows:
        title_match = re.search(
            r'<a[^>]*class="[^"]*\bgsc_a_at\b[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            row,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not title_match:
            continue

        gray_fields = [
            text_content(value)
            for value in re.findall(
                r'<div[^>]*class="[^"]*\bgs_gray\b[^"]*"[^>]*>(.*?)</div>',
                row,
                flags=re.DOTALL | re.IGNORECASE,
            )
        ]
        year_match = re.search(
            r'<span[^>]*class="[^"]*\bgsc_a_h\b[^"]*"[^>]*>(.*?)</span>',
            row,
            flags=re.DOTALL | re.IGNORECASE,
        ) or re.search(
            r'<td[^>]*class="[^"]*\bgsc_a_y\b[^"]*"[^>]*>.*?<span[^>]*>(.*?)</span>',
            row,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cited_match = re.search(
            r'<td[^>]*class="[^"]*\bgsc_a_c\b[^"]*"[^>]*>.*?<a[^>]*>(\d+)</a>',
            row,
            flags=re.DOTALL | re.IGNORECASE,
        )

        entry: dict[str, object] = {
            "title": sentence_case_title(text_content(title_match.group(2))),
            "authors": gray_fields[0] if gray_fields else "",
            "publication": gray_fields[1] if len(gray_fields) > 1 else "",
            "year": text_content(year_match.group(1)) if year_match else "",
            "scholar_url": urljoin("https://scholar.google.com", html.unescape(title_match.group(1))),
        }
        if cited_match:
            entry["cited_by"] = int(cited_match.group(1))
        publications.append(entry)

    return publications


def load_cached_extras() -> dict[str, dict[str, object]]:
    try:
        cached = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {
        normalize_title(item.get("title", "")): item
        for item in cached.get("publications", [])
        if item.get("title")
    }


def main() -> int:
    request = Request(
        PROFILE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    try:
        with urlopen(request, timeout=25) as response:
            page = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Scholar sync skipped; using cached data: {exc}", file=sys.stderr)
        return 0

    if "gsc_a_tr" not in page or "not a robot" in page.casefold():
        print("Scholar sync skipped; verification or rate limit detected.", file=sys.stderr)
        return 0

    publications = parse_profile(page)
    if not publications:
        print("Scholar sync skipped; no publication rows were found.", file=sys.stderr)
        return 0

    cached = load_cached_extras()
    for publication in publications:
        previous = cached.get(normalize_title(str(publication["title"])), {})
        for field in ("local_url", "source_url"):
            if previous.get(field):
                publication[field] = previous[field]

    payload = {
        "profile_id": PROFILE_ID,
        "profile_url": f"https://scholar.google.com/citations?user={PROFILE_ID}&hl=en",
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
        "publications": publications,
    }
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Synchronized {len(publications)} publications from Google Scholar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
