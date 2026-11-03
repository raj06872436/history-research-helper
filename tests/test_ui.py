"""The result pages escape AI and source text, and the saved examples load."""

from research import examples, ui
from research.factcheck import CheckedClaim, ClaimCheck, FactCheckResult
from research.pack import KeyFigure, Myth, ResearchPack, TimelineEvent
from research.sources import Source

SOURCES = [Source("Shivaji <b>", "https://en.wikipedia.org/wiki/Shivaji", "text")]


def test_pack_html_escapes_text_and_links_sources():
    pack = ResearchPack(
        summary="<script>alert(1)</script>",
        timeline=[TimelineEvent(date="1674", event="Crowned at Raigad", source_index=1)],
        key_figures=[KeyFigure(name="Chhatrapati Shivaji", role="King", significance="Founder", source_index=1)],
        disputed_points=["Birth year"],
        myths=[Myth(claim="Born in Delhi", reality="Born at Shivneri", source_index=1)],
        video_angles=["The coronation"],
    )
    html = ui.pack_html(pack, SOURCES)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert 'href="https://en.wikipedia.org/wiki/Shivaji"' in html
    assert ">CS<" in html  # monogram initials
    assert "Shivaji &lt;b&gt;" in html


def test_factcheck_html_shows_verdicts_and_unverified_quotes():
    check = ClaimCheck(claim="Crowned in 1774", verdict="contradicted", explanation="It was 1674.",
                       source_index=1, quote="Made-up quote")
    html = ui.factcheck_html(FactCheckResult(SOURCES, [CheckedClaim(check, SOURCES[0], False)]))
    assert 'class="claim-card contradicted"' in html
    assert "isn't in" in html
    assert "<b>1</b>contradicted" in html


def test_saved_examples_load():
    topic, pack, sources = examples.load_pack()
    script, result = examples.load_check()
    assert topic and pack.timeline and sources
    assert script and result.claims
