"""Fact-check and web source tests. No internet or API key needed."""

from types import SimpleNamespace

from research import factcheck
from research.factcheck import Claim, ClaimCheck, CheckReport, check_claims, quote_in_source
from research.sources import Source
from research import web_sources
from research.web_sources import is_trusted, page_text, search_web

SOURCES = [
    Source("Shivaji", "https://en.wikipedia.org/wiki/Shivaji",
           "Shivaji was crowned Chhatrapati of his realm on 6 June 1674 at Raigad fort.\n"
           "He was born in the hill-fort of Shivneri."),
]
CLAIMS = [Claim(text="Shivaji was crowned in 1674", search_query="Shivaji"),
          Claim(text="Shivaji was crowned in Delhi", search_query="Shivaji")]


def fake_ask(report):
    def ask(system, content, output_format, client=None):
        ask.content = content
        return report
    return ask


def test_quote_check_ignores_spacing_and_case():
    assert quote_in_source("shivaji was crowned   Chhatrapati of his realm on 6 June 1674", SOURCES[0])
    assert not quote_in_source("Shivaji was crowned in Delhi in 1674", SOURCES[0])
    assert not quote_in_source("", SOURCES[0])


def test_check_claims_flags_invented_quotes(monkeypatch):
    report = CheckReport(checks=[
        ClaimCheck(claim=CLAIMS[0].text, verdict="supported", explanation="Matches.", source_index=1,
                   quote="Shivaji was crowned Chhatrapati of his realm on 6 June 1674 at Raigad fort."),
        ClaimCheck(claim=CLAIMS[1].text, verdict="contradicted", explanation="It was Raigad.", source_index=1,
                   quote="Shivaji was crowned at the Red Fort in Delhi."),
    ])
    monkeypatch.setattr(factcheck, "ask", fake_ask(report))
    checked = check_claims(CLAIMS, SOURCES)
    assert [c.quote_verified for c in checked] == [True, False]
    assert checked[0].source is SOURCES[0]
    assert "1. Shivaji was crowned in 1674" in factcheck.ask.content


def test_check_claims_handles_missing_source(monkeypatch):
    report = CheckReport(checks=[
        ClaimCheck(claim=CLAIMS[0].text, verdict="not_found", explanation="Not covered.", source_index=0, quote=""),
    ])
    monkeypatch.setattr(factcheck, "ask", fake_ask(report))
    checked = check_claims(CLAIMS[:1], SOURCES)
    assert checked[0].source is None and not checked[0].quote_verified


def test_only_trusted_sites_are_allowed():
    assert is_trusted("https://www.worldhistory.org/Augustus/")
    assert is_trusted("britannica.com")
    assert not is_trusted("https://fakebritannica.com/page")
    assert not is_trusted("https://random-blog.net/history")


def test_page_text_keeps_paragraphs_only():
    html = """<html><nav><p>Menu link that is long enough to count as a paragraph</p></nav>
    <script>var x = 1;</script><p>Short</p>
    <p>Augustus was the first Roman emperor, reigning from 27 BCE until his death in 14 CE.</p></html>"""
    assert page_text(html) == "Augustus was the first Roman emperor, reigning from 27 BCE until his death in 14 CE."


def chunk(uri, title, domain=None):
    return SimpleNamespace(web=SimpleNamespace(uri=uri, title=title, domain=domain))


def test_search_web_keeps_trusted_pages(monkeypatch):
    metadata = SimpleNamespace(grounding_chunks=[
        chunk("https://redirect/1", "worldhistory.org"),
        chunk("https://redirect/2", "randomblog.net"),
        chunk("https://redirect/3", "historyextra.com"),
    ])
    response = SimpleNamespace(candidates=[SimpleNamespace(grounding_metadata=metadata)])
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: response))
    fetched = []

    def fake_fetch(url, title):
        fetched.append(url)
        return Source(title, f"https://{title}/page", "Real page text.") if title != "historyextra.com" else None

    monkeypatch.setattr(web_sources, "fetch_page", fake_fetch)
    sources = search_web("Roman Empire", client=client)
    assert fetched == ["https://redirect/1", "https://redirect/3"]  # the untrusted blog is never downloaded
    assert [s.title for s in sources] == ["worldhistory.org"]


def test_search_web_without_results():
    response = SimpleNamespace(candidates=[SimpleNamespace(grounding_metadata=None)])
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: response))
    assert search_web("Anything", client=client) == []
