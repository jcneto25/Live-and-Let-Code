"""Testes do resumo de baseline (read-only sobre events/decisions)."""

import json

from llc_trace.stats import format_text, load_summary, read_jsonl, summarize


def _events():
    return [
        {"kind": "step.start", "session_id": "S1", "step": "5"},
        {"kind": "step.end", "session_id": "S1", "step": "5"},
        {"kind": "step.start", "session_id": "S2", "step": "6"},
    ]


def _decisions():
    return [
        {"kind": "early_commitment", "session_id": "S1", "outcome": "llm_fallback",
         "reason": "no_classify"},
        {"kind": "early_commitment", "session_id": "S2", "outcome": "replay_hit",
         "reason": None},
        {"kind": "gate", "session_id": "S1", "outcome": "approved", "reason": "human"},
        {"kind": "gate", "session_id": "S2", "outcome": "approved",
         "reason": "auto_approve"},
    ]


def test_summarize_replay_hit_rate():
    s = summarize(_events(), _decisions())
    ec = s["early_commitment"]
    assert ec["total"] == 2
    assert ec["replay_hits"] == 1
    assert ec["replay_hit_rate"] == 0.5
    assert ec["llm_fallbacks"] == 1


def test_summarize_reasons():
    s = summarize(_events(), _decisions())
    assert s["early_commitment"]["by_reason"] == {"no_classify": 1}
    assert s["gates"]["by_reason"] == {"human": 1, "auto_approve": 1}


def test_summarize_empty_is_safe():
    s = summarize([], [])
    assert s["early_commitment"]["replay_hit_rate"] is None
    assert s["sessions"]["avg_decisions_per_session"] is None


def test_summarize_counts_events_by_kind():
    s = summarize(_events(), _decisions())
    assert s["events_by_kind"]["step.start"] == 2
    assert s["events_by_kind"]["step.end"] == 1


def test_summarize_per_session():
    s = summarize(_events(), _decisions())
    assert s["sessions"]["total"] == 2
    assert s["sessions"]["decisions_by_session"] == {"S1": 2, "S2": 2}


def test_read_jsonl_tolerates_corrupt_lines(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text(
        '{"kind":"a"}\n{nao-e-json}\n\n{"kind":"b"}\n',
        encoding="utf-8",
    )
    records, corrupt = read_jsonl(p)
    assert [r["kind"] for r in records] == ["a", "b"]
    assert corrupt == 1


def test_read_jsonl_missing_file():
    assert read_jsonl("/inexistente/events.jsonl") == ([], 0)


def test_load_summary_reads_both_files(tmp_path):
    (tmp_path / "events.jsonl").write_text(json.dumps(_events()[0]) + "\n", encoding="utf-8")
    (tmp_path / "decisions.jsonl").write_text(
        json.dumps(_decisions()[0]) + "\n", encoding="utf-8"
    )
    s = load_summary(tmp_path / "events.jsonl", tmp_path / "decisions.jsonl")
    assert s["events_total"] == 1
    assert s["decisions_total"] == 1


def test_format_text_is_human_readable():
    text = format_text(summarize(_events(), _decisions()))
    assert "LLC TRACE" in text
    assert "Hit rate: 50.0%" in text
    assert "no_classify" in text
