"""Turn source articles into a research pack using Claude."""

from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

from research.llm import ask, format_sources
from research.sources import Source


class TimelineEvent(BaseModel):
    date: str = Field(description="As precise as the sources allow, e.g. '23 January 1565' or 'c. 1336'")
    event: str
    source_index: int = Field(description="Number of the source this comes from")


class KeyFigure(BaseModel):
    name: str
    role: str = Field(description="One-line description of who they were")
    significance: str = Field(description="Why they matter to this topic, in 1-2 sentences")
    source_index: int


class Myth(BaseModel):
    claim: str = Field(description="A popular but wrong or oversimplified claim")
    reality: str = Field(description="What the sources actually say")
    source_index: int


class ResearchPack(BaseModel):
    summary: str = Field(description="3-4 sentence overview a narrator could read aloud")
    timeline: list[TimelineEvent]
    key_figures: list[KeyFigure]
    disputed_points: list[str] = Field(description="Things historians or sources disagree on")
    myths: list[Myth]
    video_angles: list[str] = Field(description="3 interesting hooks or angles for a YouTube video")


SYSTEM_PROMPT = """You are a careful research assistant for a history and geography YouTube channel.

Build a research pack using ONLY the numbered sources you are given. Do not add facts from
your own memory. Every timeline event, figure and myth must cite the source number it came from.

If the sources disagree, or give vague or approximate figures, put that in disputed_points
instead of picking one answer. Only list a myth if the sources clearly contradict it; an empty
list is fine. Keep the language simple and clear for a general audience."""


def build_pack(topic: str, sources: list[Source], client: anthropic.Anthropic | None = None) -> ResearchPack:
    """Ask Claude to build a research pack for a topic from the given sources."""
    if not sources:
        raise ValueError("No sources found for this topic. Try a different wording.")

    content = f"{format_sources(sources)}\n\nVideo topic: {topic}"
    return ask(SYSTEM_PROMPT, content, ResearchPack, client)
