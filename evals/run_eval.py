"""Measure how accurate the fact-checker is, using claims where we already know the answer.

Run from the project folder:
    python -m evals.run_eval

It makes one Gemini request per topic (6 in total), so it fits easily in the free tier.
Results are saved to evals/results/ so you can compare runs after changing a prompt.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from research.factcheck import Claim, CheckedClaim, check_claims, gather_for_claims
from research.llm import has_api_key, model_name

EVAL_DIR = Path(__file__).parent
CAUGHT = {"contradicted", "disputed"}


@dataclass
class Row:
    topic: str
    claim: str
    is_true: bool
    verdict: str
    quote_verified: bool

    @property
    def correct(self) -> bool:
        """A true claim should be supported. A false claim should be contradicted or disputed."""
        return self.verdict == "supported" if self.is_true else self.verdict in CAUGHT


def score(rows: list[Row]) -> dict:
    true_rows = [r for r in rows if r.is_true]
    false_rows = [r for r in rows if not r.is_true]
    with_quote = [r for r in rows if r.verdict != "not_found"]
    return {
        "accuracy": sum(r.correct for r in rows) / len(rows) if rows else 0.0,
        "true_confirmed": sum(r.correct for r in true_rows),
        "true_total": len(true_rows),
        "false_caught": sum(r.correct for r in false_rows),
        "false_total": len(false_rows),
        # The worst mistake: a false claim marked as supported.
        "false_marked_supported": sum(r.verdict == "supported" for r in false_rows),
        "quotes_verified": sum(r.quote_verified for r in with_quote),
        "quotes_total": len(with_quote),
    }


def rows_for_topic(topic: str, labelled: list[dict], checked: list[CheckedClaim]) -> list[Row]:
    rows = []
    for i, item in enumerate(labelled):
        # If the AI returned fewer checks than claims, count the missing ones as not found.
        result = checked[i] if i < len(checked) else None
        rows.append(Row(
            topic=topic,
            claim=item["claim"],
            is_true=item["true"],
            verdict=result.check.verdict if result else "not_found",
            quote_verified=result.quote_verified if result else False,
        ))
    return rows


def report(rows: list[Row], scores: dict) -> str:
    lines = [
        f"# Fact-checker accuracy: {datetime.now():%Y-%m-%d %H:%M} ({model_name()})",
        "",
        f"**Overall accuracy: {scores['accuracy']:.0%}**",
        "",
        f"- True claims confirmed: {scores['true_confirmed']}/{scores['true_total']}",
        f"- False claims caught: {scores['false_caught']}/{scores['false_total']}",
        f"- False claims wrongly marked supported: {scores['false_marked_supported']}",
        f"- Quotes found word for word in the source: {scores['quotes_verified']}/{scores['quotes_total']}",
        "",
        "| | Topic | Claim | Really | Verdict | Quote checked |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {'✅' if r.correct else '❌'} | {r.topic} | {r.claim} | {'true' if r.is_true else 'false'} "
            f"| {r.verdict} | {'yes' if r.quote_verified else 'no'} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--delay", type=float, default=10, help="Seconds to wait between topics (free tier limits)")
    parser.add_argument("--topic", help="Only test one topic")
    args = parser.parse_args()

    load_dotenv()
    if not has_api_key():
        raise SystemExit("No Gemini API key found. Copy .env.example to .env and paste your free key into it.")

    data = json.loads((EVAL_DIR / "claims.json").read_text(encoding="utf-8"))
    if args.topic:
        data = {args.topic: data[args.topic]}

    rows: list[Row] = []
    for n, (topic, labelled) in enumerate(data.items()):
        if n:
            time.sleep(args.delay)
        print(f"Checking {len(labelled)} claims about {topic}...")
        claims = [Claim(text=item["claim"], search_query=item["claim"]) for item in labelled]
        sources = gather_for_claims(topic, claims)
        rows += rows_for_topic(topic, labelled, check_claims(claims, sources))

    scores = score(rows)
    text = report(rows, scores)
    print("\n" + text)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    (out_dir / f"{stamp}.md").write_text(text, encoding="utf-8")
    (out_dir / f"{stamp}.json").write_text(
        json.dumps({"model": model_name(), "scores": scores, "rows": [asdict(r) for r in rows]}, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved to evals/results/{stamp}.md")


if __name__ == "__main__":
    main()
