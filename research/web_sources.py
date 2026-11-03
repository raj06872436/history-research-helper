"""Find extra sources on trusted history websites.

Gemini's Google Search finds the pages, then we download each page ourselves and keep
its real text. That way quotes from these sources can be checked word for word, just
like Wikipedia, instead of trusting the AI's own summary.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

import requests
from google import genai
from google.genai import types

from research.llm import model_name
from research.sources import HEADERS, Source

TRUSTED_DOMAINS = [
    "britannica.com",
    "worldhistory.org",
    "nationalgeographic.com",
    "smithsonianmag.com",
    "historyextra.com",
    "archive.org",
]

SEARCH_PROMPT = (
    "Search the web for reliable information about this history topic. Prefer pages from "
    + ", ".join(TRUSTED_DOMAINS)
    + ". Write a short factual summary.\n\nTopic: {topic}"
)


def is_trusted(url_or_domain: str) -> bool:
    host = urlparse(url_or_domain).hostname if "//" in url_or_domain else url_or_domain
    host = (host or "").lower()
    return any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


class _ParagraphText(HTMLParser):
    """Collect the text inside <p> tags, which is where article content lives."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.paragraphs: list[str] = []
        self.current: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "aside"):
            self.skip += 1
        elif tag == "p":
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "aside"):
            self.skip = max(0, self.skip - 1)
        elif tag == "p" and self.depth:
            self.depth -= 1
            text = " ".join("".join(self.current).split())
            if len(text) > 40:  # skip captions, buttons and other short bits
                self.paragraphs.append(text)
            self.current = []

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.current.append(data)


def page_text(html: str, max_chars: int = 15000) -> str:
    parser = _ParagraphText()
    parser.feed(html)
    text = "\n\n".join(parser.paragraphs)
    return text[:max_chars]


def fetch_page(url: str, title: str) -> Source | None:
    """Download a page and keep it only if it ends up on a trusted site and has real text."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException:
        return None  # some sites block downloads; just skip them
    if not is_trusted(response.url):
        return None
    text = page_text(response.text)
    # Very short pages are usually loading screens or menus, not articles.
    return Source(title=title, url=response.url, text=text) if len(text) >= 500 else None


def found_pages(response) -> list[tuple[str, str, str]]:
    """Return (url, title, domain) for every page Google Search used."""
    if not response.candidates or not response.candidates[0].grounding_metadata:
        return []
    pages = []
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks or []:
        if chunk.web and chunk.web.uri:
            pages.append((chunk.web.uri, chunk.web.title or "", chunk.web.domain or chunk.web.title or ""))
    return pages


def search_web(topic: str, client: genai.Client | None = None, max_pages: int = 4) -> list[Source]:
    """Search the web for a topic and return the trusted pages it found, with their real text."""
    client = client or genai.Client()
    response = client.models.generate_content(
        model=model_name(),
        contents=SEARCH_PROMPT.format(topic=topic),
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
    )
    sources: list[Source] = []
    for url, title, domain in found_pages(response):
        if len(sources) >= max_pages:
            break
        # Skip pages we already know are untrusted; unknown ones are checked after download.
        if domain and "." in domain and not is_trusted(domain):
            continue
        source = fetch_page(url, title)
        if source and all(s.url != source.url for s in sources):
            sources.append(source)
    return sources
