"""One place for calling Claude, shared by every feature."""

from __future__ import annotations

import os
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from research.sources import Source

DEFAULT_MODEL = "claude-opus-5-5"

T = TypeVar("T", bound=BaseModel)


def format_sources(sources: list[Source]) -> str:
    parts = []
    for i, source in enumerate(sources, start=1):
        parts.append(f'<source index="{i}" title="{source.title}" url="{source.url}">\n{source.text}\n</source>')
    return "\n\n".join(parts)


def ask(system: str, content: str, output_format: type[T], client: anthropic.Anthropic | None = None) -> T:
    """Send one request to Claude and get back a validated object of the given type."""
    client = client or anthropic.Anthropic()
    response = client.beta.messages.parse(
        model=os.environ.get("RESEARCH_MODEL", DEFAULT_MODEL),
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": content}],
        output_format=output_format,
        # If the main model declines a request, retry automatically on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("The AI declined this request. Try rewording it.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The answer was too long and got cut off. Try a shorter input.")
    return response.parsed_output
