"""Fetch source material from Wikipedia.

The AI only writes from these sources, never from memory, so every
fact in the research pack can be traced back to a real article.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

API_URL = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks every tool to identify itself with a User-Agent that says where it comes from.
HEADERS = {"User-Agent": "HistoryResearchHelper/0.1 (https://github.com/raj06872436/history-research-helper)"}
CACHE_DIR = Path(".cache")
MAX_ATTEMPTS = 4


@dataclass
class Source:
    title: str
    url: str
    text: str


def _get(params: dict) -> dict:
    """Call the Wikipedia API, caching results on disk so repeat lookups are free."""
    params = {**params, "format": "json", "formatversion": 2}
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    for attempt in range(MAX_ATTEMPTS):
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
        if response.status_code != 429 or attempt == MAX_ATTEMPTS - 1:
            break
        # Too many requests: wait as long as Wikipedia asks (or a growing pause), then retry.
        retry_after = response.headers.get("Retry-After", "")
        time.sleep(float(retry_after) if retry_after.isdigit() else 2 ** (attempt + 1))
    response.raise_for_status()
    data = response.json()

    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data), encoding="utf-8")
    return data


def search_titles(topic: str, limit: int = 3) -> list[str]:
    """Return the titles of the Wikipedia articles that best match a topic."""
    data = _get({"action": "query", "list": "search", "srsearch": topic, "srlimit": limit})
    return [hit["title"] for hit in data.get("query", {}).get("search", [])]


def fetch_article(title: str, max_chars: int = 15000) -> Source | None:
    """Fetch the plain text of one article. Long articles are cut to max_chars."""
    data = _get({
        "action": "query",
        "prop": "extracts|info",
        "explaintext": 1,
        "inprop": "url",
        "redirects": 1,
        "titles": title,
    })
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    page = pages[0]
    text = page.get("extract", "")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... article continues ...]"
    return Source(title=page["title"], url=page["fullurl"], text=text)


def gather_sources(topic: str, max_articles: int = 3) -> list[Source]:
    """Find and fetch the most relevant articles for a topic."""
    sources = []
    for title in search_titles(topic, limit=max_articles):
        source = fetch_article(title)
        if source and source.text.strip():
            sources.append(source)
    return sources

