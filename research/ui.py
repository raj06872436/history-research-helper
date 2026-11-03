"""The look of the app: an atlas-inspired theme and HTML for each result section.

Everything the AI or a source wrote is escaped before it goes into HTML.
"""

from __future__ import annotations

import math
from base64 import b64encode
from html import escape

from research.factcheck import FactCheckResult
from research.pack import ResearchPack
from research.sources import Source

VERDICTS = {
    "supported": "Supported",
    "disputed": "Disputed",
    "contradicted": "Contradicted",
    "not_found": "No source found",
}


def _contours() -> str:
    """Faint topographic contour lines, drawn once as an SVG background."""
    paths = []
    for ring in range(9):
        radius = 26 + ring * 17
        points = []
        for step in range(73):
            a = step / 72 * 2 * math.pi
            wobble = 1 + 0.10 * math.sin(3 * a + ring * 0.5) + 0.06 * math.sin(5 * a - ring * 0.8)
            points.append(f"{340 + radius * 1.6 * wobble * math.cos(a):.1f},{150 + radius * wobble * math.sin(a):.1f}")
        paths.append(f'<path d="M{" L".join(points)} Z"/>')
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300">'
        '<g fill="none" stroke="#17344B" stroke-opacity="0.13" stroke-width="1.2">'
        + "".join(paths)
        + "</g></svg>"
    )
    return "data:image/svg+xml;base64," + b64encode(svg.encode()).decode()


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,500;0,700;1,400&family=Alegreya+Sans:wght@400;500;700&display=swap');

:root {
  --sea: #D9E4E1;
  --paper: #F6F8F5;
  --ink: #17344B;
  --ink-soft: #4A6275;
  --rule: #B9CAC6;
  --supported: #2F6B4F;
  --disputed: #A86F14;
  --contradicted: #B0362B;
  --not_found: #5E7182;
  --serif: 'Alegreya', Georgia, serif;
  --sans: 'Alegreya Sans', 'Segoe UI', sans-serif;
}

.stApp { background: var(--sea); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1040px; padding-top: 2.5rem; padding-bottom: 5rem; }
html, body, .stApp, .stMarkdown, button, input, textarea, label, [data-baseweb="tab"] {
  font-family: var(--sans) !important;
}
.stMarkdown p, .stMarkdown li { font-size: 1.06rem; }

/* Header */
.atlas-hero {
  position: relative;
  padding: 2.2rem 0 1.6rem;
  margin-bottom: 0.4rem;
  background: url("CONTOURS") right -40px center / 620px auto no-repeat;
}
.atlas-hero h1 {
  font-family: var(--serif) !important;
  font-weight: 700;
  font-size: clamp(2.3rem, 5vw, 3.4rem);
  line-height: 1.05;
  color: var(--ink);
  margin: 0 0 0.6rem;
  padding: 0;
  letter-spacing: -0.01em;
}
.atlas-hero p {
  font-family: var(--serif);
  font-style: italic;
  font-size: 1.25rem;
  color: var(--ink-soft);
  max-width: 34rem;
  margin: 0;
}

/* Tabs, forms, buttons */
[data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--rule); }
[data-baseweb="tab"] { font-size: 1.08rem !important; color: var(--ink-soft); padding: 0.5rem 0; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--ink); font-weight: 700; }
[data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 3px; }
[data-testid="stForm"] {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: 10px;
  padding: 1.4rem 1.5rem 1.2rem;
}
.stButton button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {
  border-radius: 999px;
  font-weight: 700;
  padding: 0.45rem 1.3rem;
  border: 1.5px solid var(--ink);
}
[data-testid="stFormSubmitButton"] button { background: var(--ink); color: var(--paper); }
[data-testid="stFormSubmitButton"] button:hover { background: #0F2638; color: var(--paper); border-color: #0F2638; }
.stButton button, [data-testid="stDownloadButton"] button { background: transparent; color: var(--ink); }
button:focus-visible, input:focus-visible, textarea:focus-visible, a:focus-visible {
  outline: 3px solid var(--disputed) !important;
  outline-offset: 2px;
}

/* Result sections */
.atlas-section { margin: 2.6rem 0 0; }
.atlas-section h2 {
  font-family: var(--serif) !important;
  font-weight: 500;
  font-size: 1.75rem;
  color: var(--ink);
  margin: 0 0 0.2rem;
  padding: 0;
}
.atlas-section [data-testid="stHeaderActionElements"], .atlas-hero [data-testid="stHeaderActionElements"] { display: none; }
.atlas-section .note { color: var(--ink-soft); font-size: 0.98rem; margin: 0 0 1.1rem; }
.lead {
  font-family: var(--serif);
  font-size: 1.42rem;
  line-height: 1.55;
  color: var(--ink);
  max-width: 44rem;
  margin: 2rem 0 0;
}
sup.cite a {
  font-family: var(--sans);
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 0 0.3rem;
  margin-left: 0.15rem;
  text-decoration: none;
}
sup.cite a:hover { background: var(--ink); color: var(--paper); }

/* The timeline drawn as a route */
.route { list-style: none; margin: 0.4rem 0 0 0.5rem; padding: 0 0 0 1.8rem; border-left: 2px dashed var(--ink-soft); }
.route li { position: relative; margin: 0 0 1.35rem; max-width: 42rem; }
.route li::before {
  content: "";
  position: absolute;
  left: calc(-1.8rem - 9px);
  top: 0.32rem;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--paper);
  border: 3px solid var(--ink);
}
.route li:last-child { margin-bottom: 0; }
.route li:last-child::before { background: var(--ink); }
.route .when { font-family: var(--serif); font-weight: 700; font-size: 1.12rem; color: var(--ink); }
.route .what { font-size: 1.06rem; line-height: 1.5; color: var(--ink); }

/* People */
.people { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 1.4rem 2.2rem; }
.person { display: grid; grid-template-columns: 3rem 1fr; gap: 0.9rem; align-items: start; }
.monogram {
  width: 3rem; height: 3rem; border-radius: 50%;
  display: grid; place-items: center;
  font-family: var(--serif); font-weight: 700; font-size: 1.15rem;
  color: var(--paper); background: var(--ink);
}
.person .name { font-family: var(--serif); font-weight: 700; font-size: 1.15rem; line-height: 1.2; }
.person .role { font-family: var(--serif); font-style: italic; color: var(--ink-soft); margin-bottom: 0.25rem; }
.person .why { font-size: 1rem; line-height: 1.5; }

/* Disputes and myths */
.notes-list { list-style: none; padding: 0; margin: 0; max-width: 44rem; }
.notes-list li { border-left: 4px solid var(--disputed); background: var(--paper); padding: 0.75rem 1rem; margin-bottom: 0.6rem; border-radius: 0 6px 6px 0; line-height: 1.5; }
.myth { max-width: 44rem; margin-bottom: 1.3rem; display: grid; grid-template-columns: 1.6rem 1fr; gap: 0.15rem 0.6rem; }
.myth .mark { width: 1.35rem; height: 1.35rem; border-radius: 50%; display: grid; place-items: center; font-size: 0.8rem; font-weight: 700; color: var(--paper); margin-top: 0.2rem; }
.myth .mark.no { background: var(--contradicted); }
.myth .mark.yes { background: var(--supported); }
.myth .claim { font-family: var(--serif); font-size: 1.15rem; line-height: 1.4; color: var(--contradicted); }
.myth .reality { line-height: 1.5; }
.angles { padding-left: 1.2rem; max-width: 44rem; }
.angles li { font-family: var(--serif); font-size: 1.18rem; line-height: 1.45; margin-bottom: 0.6rem; }
.angles li::marker { color: var(--ink-soft); }

/* Sources, as footnotes */
.footnotes { padding-left: 1.6rem; margin: 0; columns: 2 300px; column-gap: 2.5rem; }
.footnotes li { margin-bottom: 0.4rem; break-inside: avoid; color: var(--ink-soft); }
.footnotes a { color: var(--ink); }

/* Fact-check */
.scalebar { display: flex; height: 14px; border: 2px solid var(--ink); border-radius: 2px; overflow: hidden; max-width: 44rem; margin-top: 2rem; }
.scalebar span + span { border-left: 2px solid var(--paper); }
.legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem; margin: 0.7rem 0 0; font-size: 1.02rem; }
.legend b { font-family: var(--serif); font-size: 1.3rem; margin-right: 0.25rem; }
.dot { display: inline-block; width: 0.7rem; height: 0.7rem; border-radius: 50%; margin-right: 0.4rem; vertical-align: 0.05rem; }
.bg-supported { background: var(--supported); }
.bg-disputed { background: var(--disputed); }
.bg-contradicted { background: var(--contradicted); }
.bg-not_found { background: var(--not_found); }

.claim-card { background: var(--paper); border-left: 5px solid var(--verdict); border-radius: 0 8px 8px 0; padding: 1rem 1.25rem; margin: 0 0 0.9rem; max-width: 50rem; }
.claim-card.supported { --verdict: var(--supported); }
.claim-card.disputed { --verdict: var(--disputed); }
.claim-card.contradicted { --verdict: var(--contradicted); }
.claim-card.not_found { --verdict: var(--not_found); }
.claim-card .verdict { font-weight: 700; color: var(--verdict); font-size: 0.98rem; }
.claim-card .text { font-family: var(--serif); font-size: 1.24rem; line-height: 1.4; margin: 0.15rem 0 0.4rem; }
.claim-card .why { line-height: 1.5; color: var(--ink); }
.claim-card blockquote {
  font-family: var(--serif); font-style: italic; font-size: 1.05rem; line-height: 1.5;
  margin: 0.7rem 0 0.3rem; padding: 0 0 0 0.9rem; border-left: 2px solid var(--rule); color: var(--ink);
}
.claim-card blockquote, .claim-card blockquote * { color: var(--ink) !important; }
.claim-card .provenance { font-size: 0.95rem; color: var(--ink-soft); }
.claim-card .provenance.unverified { color: var(--contradicted); font-weight: 500; }
.claim-card .provenance a { color: inherit; }

.example-script { font-family: var(--serif); font-style: italic; font-size: 1.08rem; line-height: 1.55; max-width: 44rem; margin: 0.4rem 0 0; padding-left: 1rem; border-left: 3px solid var(--rule); color: var(--ink-soft); }
[data-testid="stAlert"] { max-width: 50rem; }
[data-testid="stAlertContainer"] { background: var(--paper) !important; border: 1px solid var(--rule); border-radius: 8px; }
[data-testid="stAlertContainer"] p { color: var(--ink) !important; }

.empty { max-width: 40rem; margin: 2rem 0 0.9rem; color: var(--ink-soft); font-size: 1.08rem; line-height: 1.55; }
.empty strong { color: var(--ink); }

@media (max-width: 640px) {
  .atlas-hero { background-size: 420px auto; background-position: right -120px top 0; }
  .lead { font-size: 1.2rem; }
  .footnotes { columns: 1; }
}
</style>
""".replace("CONTOURS", _contours())


def header() -> str:
    return (
        '<header class="atlas-hero"><h1>History Research Helper</h1>'
        "<p>Sourced research and claim-by-claim fact-checks for history and geography videos.</p></header>"
    )


def _cite(index: int, sources: list[Source]) -> str:
    if 1 <= index <= len(sources):
        s = sources[index - 1]
        return f'<sup class="cite"><a href="{escape(s.url)}" target="_blank" title="{escape(s.title)}">{index}</a></sup>'
    return ""


def _section(title: str, body: str, note: str = "") -> str:
    note_html = f'<p class="note">{escape(note)}</p>' if note else ""
    return f'<section class="atlas-section"><h2>{escape(title)}</h2>{note_html}{body}</section>'


def _initials(name: str) -> str:
    words = [w for w in name.replace("-", " ").split() if w[:1].isalpha()]
    return escape("".join(w[0].upper() for w in (words[:1] + words[-1:] if len(words) > 1 else words)) or "?")


def sources_section(sources: list[Source]) -> str:
    items = "".join(
        f'<li><a href="{escape(s.url)}" target="_blank">{escape(s.title)}</a></li>' for s in sources
    )
    return _section("Sources", f'<ol class="footnotes">{items}</ol>', "The numbers next to each fact point here.")


def pack_html(pack: ResearchPack, sources: list[Source]) -> str:
    parts = [f'<p class="lead">{escape(pack.summary)}</p>']

    stops = "".join(
        f'<li><div class="when">{escape(e.date)}</div>'
        f'<div class="what">{escape(e.event)}{_cite(e.source_index, sources)}</div></li>'
        for e in pack.timeline
    )
    parts.append(_section("Timeline", f'<ol class="route">{stops}</ol>', "Dates as precise as the sources give them."))

    people = "".join(
        f'<div class="person"><div class="monogram" aria-hidden="true">{_initials(f.name)}</div><div>'
        f'<div class="name">{escape(f.name)}</div><div class="role">{escape(f.role)}</div>'
        f'<div class="why">{escape(f.significance)}{_cite(f.source_index, sources)}</div></div></div>'
        for f in pack.key_figures
    )
    parts.append(_section("Key figures", f'<div class="people">{people}</div>'))

    if pack.disputed_points:
        items = "".join(f"<li>{escape(d)}</li>" for d in pack.disputed_points)
        parts.append(_section(
            "Where sources disagree", f'<ul class="notes-list">{items}</ul>',
            "Say these carefully in your video, or mention the debate.",
        ))

    if pack.myths:
        myths = "".join(
            f'<div class="myth"><span class="mark no" aria-label="Myth">✕</span><div class="claim">{escape(m.claim)}</div>'
            f'<span class="mark yes" aria-label="What the sources say">✓</span>'
            f'<div class="reality">{escape(m.reality)}{_cite(m.source_index, sources)}</div></div>'
            for m in pack.myths
        )
        parts.append(_section("Myths to avoid", myths, "Popular claims the sources don't back up."))

    angles = "".join(f"<li>{escape(a)}</li>" for a in pack.video_angles)
    parts.append(_section("Video angles", f'<ul class="angles">{angles}</ul>', "Starting points for a hook or title."))
    parts.append(sources_section(sources))
    return "".join(parts)


def factcheck_html(result: FactCheckResult) -> str:
    counts = {v: sum(c.check.verdict == v for c in result.claims) for v in VERDICTS}
    bar = "".join(
        f'<span class="bg-{v}" style="flex:{n}" title="{n} {VERDICTS[v].lower()}"></span>'
        for v, n in counts.items() if n
    )
    legend = "".join(
        f'<span><i class="dot bg-{v}"></i><b>{n}</b>{escape(VERDICTS[v].lower())}</span>' for v, n in counts.items()
    )
    parts = [
        f'<div class="scalebar" role="img" aria-label="Verdicts for {len(result.claims)} claims">{bar}</div>'
        f'<div class="legend">{legend}</div>'
    ]

    cards = []
    for c in result.claims:
        v = c.check.verdict
        quote = provenance = ""
        if c.source and c.check.quote:
            link = f'<a href="{escape(c.source.url)}" target="_blank">{escape(c.source.title)}</a>'
            quote = f"<blockquote>{escape(c.check.quote)}</blockquote>"
            if c.quote_verified:
                provenance = f'<div class="provenance">Matched word for word in {link}</div>'
            else:
                provenance = (
                    f'<div class="provenance unverified">This quote isn\'t in {link} word for word. '
                    "Check the source before relying on it.</div>"
                )
        cards.append(
            f'<article class="claim-card {v}"><div class="verdict">{VERDICTS[v]}</div>'
            f'<div class="text">{escape(c.check.claim)}</div><div class="why">{escape(c.check.explanation)}</div>'
            f"{quote}{provenance}</article>"
        )
    parts.append(_section("Claims", "".join(cards), "In the order they appear in your script."))
    parts.append(sources_section(result.sources))
    return "".join(parts)


def empty_state(what: str) -> str:
    return f'<div class="empty">{what}</div>'
