"""One place for calling the AI (Google Gemini), shared by every feature."""

from __future__ import annotations

import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from research.sources import Source

# Free on Google AI Studio's free tier. Change it with GEMINI_MODEL in your .env file.
DEFAULT_MODEL = "gemini-2.5-flash"

T = TypeVar("T", bound=BaseModel)

BLOCKED_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}


def model_name() -> str:
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def has_api_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def format_sources(sources: list[Source]) -> str:
    parts = []
    for i, source in enumerate(sources, start=1):
        parts.append(f'<source index="{i}" title="{source.title}" url="{source.url}">\n{source.text}\n</source>')
    return "\n\n".join(parts)


def finish_reason(response) -> str:
    if not response.candidates:
        return "BLOCKED"
    reason = response.candidates[0].finish_reason
    return getattr(reason, "name", str(reason))


def ask(system: str, content: str, output_format: type[T], client: genai.Client | None = None) -> T:
    """Send one request to Gemini and get back a validated object of the given type."""
    client = client or genai.Client()  # reads GEMINI_API_KEY from the environment
    response = client.models.generate_content(
        model=model_name(),
        contents=content,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=output_format,
        ),
    )

    if response.parsed is not None:
        return response.parsed
    reason = finish_reason(response)
    if reason == "MAX_TOKENS":
        raise RuntimeError("The answer was too long and got cut off. Try a shorter input.")
    if reason in BLOCKED_REASONS or reason == "BLOCKED":
        raise RuntimeError("The AI declined this request. Try rewording it.")
    raise RuntimeError("The AI sent back an answer in the wrong format. Please try again.")
