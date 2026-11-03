"""Tests for the accuracy scorer. No internet or API key needed."""

import json
from pathlib import Path

from evals.run_eval import Row, rows_for_topic, score
from research.factcheck import CheckedClaim, ClaimCheck


def row(is_true, verdict, quote_verified=True):
    return Row("Topic", "A claim", is_true, verdict, quote_verified)


def test_scoring_rules():
    rows = [
        row(True, "supported"),        # correct
        row(True, "not_found", False), # missed
        row(False, "contradicted"),    # caught
        row(False, "disputed"),        # caught
        row(False, "supported"),       # worst mistake
        row(False, "not_found", False),# not caught
    ]
    s = score(rows)
    assert s["true_confirmed"] == 1 and s["true_total"] == 2
    assert s["false_caught"] == 2 and s["false_total"] == 4
    assert s["false_marked_supported"] == 1
    assert s["quotes_verified"] == 4 and s["quotes_total"] == 4
    assert s["accuracy"] == 3 / 6


def test_missing_checks_count_as_not_found():
    labelled = [{"claim": "One", "true": True}, {"claim": "Two", "true": False}]
    check = ClaimCheck(claim="One", verdict="supported", explanation="", source_index=1, quote="q")
    rows = rows_for_topic("T", labelled, [CheckedClaim(check, None, True)])
    assert [r.verdict for r in rows] == ["supported", "not_found"]


def test_claim_file_is_valid():
    data = json.loads((Path(__file__).parent.parent / "evals" / "claims.json").read_text(encoding="utf-8"))
    claims = [c for topic in data.values() for c in topic]
    assert len(claims) >= 30
    assert all(isinstance(c["claim"], str) and isinstance(c["true"], bool) for c in claims)
    assert any(c["true"] for c in claims) and any(not c["true"] for c in claims)
