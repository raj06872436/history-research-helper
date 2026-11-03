"""Fact-check a video script, claim by claim, against real sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from google import genai
from pydantic import BaseModel, Field

from research.llm import ask, format_sources
from research.sources import Source, fetch_article, search_titles


class Claim(BaseModel):
    text: str = Field(description="One checkable factual claim, rewritten to stand on its own")
    search_query: str = Field(description="A short Wikipedia search query to find evidence for this claim")


class ClaimList(BaseModel):
    claims: list[Claim]


Verdict = Literal["supported", "disputed", "contradicted", "not_found"]


class ClaimCheck(BaseModel):
    claim: str
    verdict: Verdict
    explanation: str = Field(description="One or two sentences on why, in plain language")
    source_index: int = Field(description="Number of the source used, or 0 if no source covers the claim")
    quote: str = Field(description="Exact sentence copied word for word from that source, or empty if none")


class CheckReport(BaseModel):
    checks: list[ClaimCheck]


@dataclass
class CheckedClaim:
    check: ClaimCheck
    source: Source | None
    # True when the quote really appears in the cited source, so the AI did not invent it.
    quote_verified: bool


@dataclass
class FactCheckResult:
    sources: list[Source]
    claims: list[CheckedClaim]


EXTRACT_PROMPT = """You split video scripts into individual factual claims that can be checked.

Pick out every statement of fact: dates, numbers, names, places, causes and events.
Skip opinions, jokes, questions and calls to action. Rewrite each claim so it makes
sense on its own (replace "he" or "it" with the actual name)."""

CHECK_PROMPT = """You are a strict fact-checker for a history and geography YouTube channel.

Check each claim using ONLY the numbered sources. Never use your own memory.
- supported: a source clearly says the same thing.
- contradicted: a source clearly says something different (a different date, person or number).
- disputed: sources disagree with each other, or describe the point as uncertain or debated.
- not_found: no source covers the claim. Use this even if you believe the claim is true.

For every verdict except not_found, copy the exact sentence from the source that backs your
verdict into quote, word for word, without changing or shortening it. Return one check per
claim, in the same order as the claims."""


def extract_claims(script: str, client: genai.Client | None = None) -> list[Claim]:
    if not script.strip():
        raise ValueError("The script is empty.")
    return ask(EXTRACT_PROMPT, f"<script>\n{script}\n</script>", ClaimList, client).claims


def gather_for_claims(topic: str, claims: list[Claim], max_articles: int = 6) -> list[Source]:
    """Fetch articles for the overall topic first, then for each claim's own search query."""
    queries = [topic] + [c.search_query for c in claims] if topic.strip() else [c.search_query for c in claims]
    titles: list[str] = []
    for query in queries:
        for title in search_titles(query, limit=2 if query == topic else 1):
            if title not in titles:
                titles.append(title)
    sources = []
    for title in titles:
        if len(sources) >= max_articles:
            break
        source = fetch_article(title)
        if source and source.text.strip():
            sources.append(source)
    return sources


def _normalise(text: str) -> str:
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[\"“”]", "", text)
    return re.sub(r"\s+", " ", text).strip(" .")


def quote_in_source(quote: str, source: Source) -> bool:
    """Check that a quote really appears in the source text (ignoring spacing, case and quote marks)."""
    return bool(quote.strip()) and _normalise(quote) in _normalise(source.text)


def check_claims(
    claims: list[Claim], sources: list[Source], client: genai.Client | None = None
) -> list[CheckedClaim]:
    if not claims:
        return []
    if not sources:
        raise ValueError("No sources found to check against. Try adding a topic.")
    claim_lines = "\n".join(f"{i}. {c.text}" for i, c in enumerate(claims, start=1))
    content = f"{format_sources(sources)}\n\n<claims>\n{claim_lines}\n</claims>"
    report = ask(CHECK_PROMPT, content, CheckReport, client)

    checked = []
    for check in report.checks:
        source = sources[check.source_index - 1] if 1 <= check.source_index <= len(sources) else None
        verified = source is not None and quote_in_source(check.quote, source)
        checked.append(CheckedClaim(check=check, source=source, quote_verified=verified))
    return checked


def fact_check(
    script: str,
    topic: str = "",
    client: genai.Client | None = None,
    extra_sources: list[Source] | None = None,
) -> FactCheckResult:
    """Full pipeline: split the script into claims, find sources, check every claim."""
    claims = extract_claims(script, client)
    sources = gather_for_claims(topic, claims) + (extra_sources or [])
    return FactCheckResult(sources=sources, claims=check_claims(claims, sources, client))
