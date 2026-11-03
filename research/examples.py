"""Saved example results, so the app can show what it does without using any AI requests."""

from __future__ import annotations

import json
from pathlib import Path

from research.factcheck import CheckedClaim, ClaimCheck, FactCheckResult
from research.pack import ResearchPack
from research.sources import Source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
PACK_FILE = EXAMPLES_DIR / "research_pack.json"
CHECK_FILE = EXAMPLES_DIR / "fact_check.json"


def _source(data: dict) -> Source:
    # Source text isn't saved, to keep the files small; the quote checks were done when saved.
    return Source(title=data["title"], url=data["url"], text="")


def save_pack(topic: str, pack: ResearchPack, sources: list[Source]) -> None:
    EXAMPLES_DIR.mkdir(exist_ok=True)
    data = {"topic": topic, "pack": pack.model_dump(), "sources": [{"title": s.title, "url": s.url} for s in sources]}
    PACK_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_pack() -> tuple[str, ResearchPack, list[Source]]:
    data = json.loads(PACK_FILE.read_text(encoding="utf-8"))
    return data["topic"], ResearchPack.model_validate(data["pack"]), [_source(s) for s in data["sources"]]


def save_check(script: str, result: FactCheckResult) -> None:
    EXAMPLES_DIR.mkdir(exist_ok=True)
    data = {
        "script": script,
        "sources": [{"title": s.title, "url": s.url} for s in result.sources],
        "claims": [
            {"check": c.check.model_dump(), "source_index": result.sources.index(c.source) if c.source else None,
             "quote_verified": c.quote_verified}
            for c in result.claims
        ],
    }
    CHECK_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_check() -> tuple[str, FactCheckResult]:
    data = json.loads(CHECK_FILE.read_text(encoding="utf-8"))
    sources = [_source(s) for s in data["sources"]]
    claims = [
        CheckedClaim(
            check=ClaimCheck.model_validate(c["check"]),
            source=sources[c["source_index"]] if c["source_index"] is not None else None,
            quote_verified=c["quote_verified"],
        )
        for c in data["claims"]
    ]
    return data["script"], FactCheckResult(sources=sources, claims=claims)
