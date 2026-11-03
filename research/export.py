"""Turn results into Markdown files you can download into your script notes."""

from research.factcheck import FactCheckResult
from research.pack import ResearchPack
from research.sources import Source

VERDICT_LABELS = {
    "supported": "✅ Supported",
    "disputed": "⚠️ Disputed",
    "contradicted": "❌ Contradicted",
    "not_found": "❓ No source found",
}


def to_markdown(topic: str, pack: ResearchPack, sources: list[Source]) -> str:
    """Plain-text version of the research pack."""
    lines = [f"# Research pack: {topic}", "", pack.summary, "", "## Timeline"]
    lines += [f"- **{e.date}**: {e.event} [{e.source_index}]" for e in pack.timeline]
    lines += ["", "## Key figures"]
    lines += [f"- **{f.name}** ({f.role}): {f.significance} [{f.source_index}]" for f in pack.key_figures]
    if pack.disputed_points:
        lines += ["", "## Disputed points"] + [f"- {d}" for d in pack.disputed_points]
    if pack.myths:
        lines += ["", "## Myths to avoid"]
        lines += [f"- Myth: {m.claim}\n  Reality: {m.reality} [{m.source_index}]" for m in pack.myths]
    lines += ["", "## Video angles"] + [f"- {a}" for a in pack.video_angles]
    lines += ["", "## Sources"] + [f"{i}. {s.title}: {s.url}" for i, s in enumerate(sources, 1)]
    return "\n".join(lines)


def factcheck_to_markdown(result: FactCheckResult) -> str:
    lines = ["# Fact-check report", ""]
    for c in result.claims:
        lines.append(f"- {VERDICT_LABELS[c.check.verdict]}: {c.check.claim}")
        lines.append(f"  - {c.check.explanation}")
        if c.source:
            lines.append(f'  - "{c.check.quote}" ({c.source.title}: {c.source.url})')
    return "\n".join(lines)
