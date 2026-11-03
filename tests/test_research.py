"""Tests that run without internet or an API key."""

from types import SimpleNamespace

import pytest

from app import to_markdown
from research.llm import format_sources
from research.pack import KeyFigure, ResearchPack, TimelineEvent, build_pack
from research.sources import Source

SOURCES = [
    Source("Battle of Talikota", "https://en.wikipedia.org/wiki/Battle_of_Talikota", "Fought in 1565."),
    Source("Vijayanagara Empire", "https://en.wikipedia.org/wiki/Vijayanagara_Empire", "Founded c. 1336."),
]

PACK = ResearchPack(
    summary="A short summary.",
    timeline=[TimelineEvent(date="1565", event="Battle of Talikota", source_index=1)],
    key_figures=[KeyFigure(name="Rama Raya", role="Regent", significance="Led the army.", source_index=1)],
    disputed_points=[],
    myths=[],
    video_angles=["Why one battle ended an empire"],
)


class FakeMessages:
    def __init__(self, stop_reason="end_turn"):
        self.stop_reason = stop_reason
        self.last_request = None

    def parse(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(stop_reason=self.stop_reason, parsed_output=PACK)


def fake_client(stop_reason="end_turn"):
    return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(stop_reason)))


def test_sources_are_numbered_from_one():
    text = format_sources(SOURCES)
    assert '<source index="1" title="Battle of Talikota"' in text
    assert '<source index="2" title="Vijayanagara Empire"' in text


def test_build_pack_sends_sources_and_topic():
    client = fake_client()
    pack = build_pack("Fall of Vijayanagara", SOURCES, client=client)
    assert pack is PACK
    prompt = client.beta.messages.last_request["messages"][0]["content"]
    assert "Founded c. 1336." in prompt
    assert prompt.endswith("Video topic: Fall of Vijayanagara")


def test_build_pack_needs_sources():
    with pytest.raises(ValueError):
        build_pack("Anything", [], client=fake_client())


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_build_pack_reports_unusable_responses(stop_reason):
    with pytest.raises(RuntimeError):
        build_pack("Anything", SOURCES, client=fake_client(stop_reason))


def test_markdown_export_lists_sources():
    md = to_markdown("Fall of Vijayanagara", PACK, SOURCES)
    assert "**1565**: Battle of Talikota [1]" in md
    assert "1. Battle of Talikota: https://en.wikipedia.org/wiki/Battle_of_Talikota" in md
