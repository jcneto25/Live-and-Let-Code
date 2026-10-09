"""Testes para llc_replay.verify — Fase 7: Deterministic Replay."""

import os
import json
import tempfile
from pathlib import Path

import pytest

# Configurar ambiente de teste
os.environ["LLC_TRACE"] = "1"
os.environ["LLC2_CLASSIFY"] = "1"
os.environ["LLC2_DELTA"] = "1"
os.environ["LLC2_STATECHART"] = "1"
os.environ["LLC2_DOC_JUDGE"] = "1"

from llc_replay.verify import (
    load_decision_records,
    find_matching_record,
    attempt_replay,
    log_replay_attempt,
)
from llc2.contracts import (
    canonical_hash,
    load_policy,
    Automation,
    Decision,
    DecisionRecord,
    RiskClass,
)
from llc_trace import decisions_path


@pytest.fixture(autouse=True)
def isolate_replay_logs(monkeypatch, tmp_path):
    monkeypatch.setenv("LLC_TRACE_DIR", str(tmp_path / "trace"))
    # O default do classificador é 0 (§9 do plano). Estes testes cobrem o
    # caminho de replay LIGADO — sem a flag, os testes de fallback passariam
    # por omissão (replay desligado). `monkeypatch` restaura a env ao fim de
    # cada teste: nada vaza para as demais suítes e não há dependência da
    # ordem de importação.
    monkeypatch.setenv("LLC2_REPLAY", "1")


def _write_test_decisions(records: list[dict]):
    """Helper para escrever records de teste no arquivo decisions.jsonl."""
    log_path = decisions_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup original se existir
    backup = None
    if log_path.exists():
        backup = log_path.read_text()
    
    with open(log_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    
    return backup


def _restore_decisions(backup: str | None):
    """Restaura o arquivo decisions.jsonl original."""
    log_path = decisions_path()
    if backup is not None:
        log_path.write_text(backup)
    elif log_path.exists():
        log_path.unlink()


_TASK_TYPES = ("crud_endpoint", "ui_component", "validation_rule",
               "test_write", "unknown")


def _choice_transport(choice: str, confidence: float):
    """Transport scriptado (API canônica `FakeJevTransport({...})`).

    Uma única Choice de `task_type` com distribuição normalizada — este é o
    formato usado pelos testes de contrato em `llc2/tests/test_classifier.py`.
    """
    from llc2.jev_adapter import FakeJevTransport

    others = (1.0 - confidence) / (len(_TASK_TYPES) - 1)
    probabilities = {t: (confidence if t == choice else others)
                     for t in _TASK_TYPES}
    return FakeJevTransport({
        "task_type": {
            "choice": choice,
            "probabilities": probabilities,
            "confidence": confidence,
        },
    })


# ── Test Data Fixtures ────────────────────────────────────────────────────────

def make_test_record(
    input_hash: str = "sha256:test123",
    kind: str = "early_commitment",
    automation: str = "AUTO",
    policy_version: str = "1.0.0",
    thresholds_hash: str = "sha256:abc123",
    statechart_to: str = "active",
    config_extra: dict | None = None,
) -> dict:
    """Cria um DecisionRecord de teste válido."""
    record = {
        "schema": "llc-trace-decision/0.1",
        "decision_id": "test-decision-id",
        "ts": "2026-10-08T15:14:54",
        "pid": 12345,
        "kind": kind,
        "session_id": "test-session",
        "step": "5",
        "state": "STEP_EXECUTION",
        "event": "CLASSIFY",
        "input_hash": input_hash,
        "state_hash": None,
        "inputs": {"task": "Criar endpoint de teste"},
        "evidence": {
            "classification_type": "crud_endpoint",
            "classification_confidence": 0.92,
            "routing": automation,
        },
        "outcome": "classify",
        "reason": "semantic_confident",
        "automation": automation,
        "policy_version": policy_version,
        "statechart_version": None,
        "jev_model": "jev-1.13.0",
        "jev_request_id": "req-test",
        # Evidência coerente com reason="semantic_confident" e automation=AUTO:
        # sem ela o registro é internamente inconsistente e o replay (que
        # recomputa a partir da evidência gravada) não pode reproduzi-lo.
        "jev_result": {
            "model": "jev-1.13.0",
            "request_id": "req-test",
            "answers": {
                "task_type": {
                    "type": "choice",
                    "choice": "crud_endpoint",
                    "probabilities": {
                        "crud_endpoint": 0.92, "ui_component": 0.02,
                        "validation_rule": 0.02, "test_write": 0.02,
                        "unknown": 0.02,
                    },
                    "confidence": 0.92,
                },
            },
            "usage": {"input_tokens": 1200, "output_tokens": 40},
        },
        "hard_eval": None,
        "human_approval": None,
        "runtime_version": "llc-1.x",
        "config": {
            "policy_id": "llc-default",
            "policy_version": policy_version,
            "question_set_hash": "sha256:qshash",
            "question_set_version": "2.0.0",
            "thresholds_hash": thresholds_hash,
        },
        "statechart": {
            "from": "idle",
            "to": statechart_to,
            "guard": "guard_hard_eval_passed",
            "guard_result": True,
        },
        "action": None,
        "artifact_hashes": [],
    }
    
    if config_extra:
        record["config"].update(config_extra)
    
    return record


# ── Tests for load_decision_records ──────────────────────────────────────────

def test_load_decision_records_empty():
    """Carregar de arquivo inexistente retorna lista vazia."""
    backup = _write_test_decisions([])
    try:
        records = load_decision_records()
        assert records == []
    finally:
        _restore_decisions(backup)


def test_load_decision_records_multiple():
    """Carrega múltiplos records do JSONL."""
    records = [
        make_test_record(input_hash="sha256:aaa"),
        make_test_record(input_hash="sha256:bbb"),
    ]
    backup = _write_test_decisions(records)
    try:
        loaded = load_decision_records()
        assert len(loaded) == 2
        assert loaded[0]["input_hash"] == "sha256:aaa"
        assert loaded[1]["input_hash"] == "sha256:bbb"
    finally:
        _restore_decisions(backup)


def test_load_decision_records_uses_trace_directory():
    record = make_test_record(input_hash="sha256:isolated")
    backup = _write_test_decisions([record])
    try:
        assert load_decision_records() == [record]
    finally:
        _restore_decisions(backup)


def test_load_decision_records_ignores_corrupt_lines():
    """Linhas JSON inválidas são ignoradas silenciosamente."""
    log_path = decisions_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    backup = log_path.read_text() if log_path.exists() else None
    
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write('{"valid": "json"}\n')
            f.write('not json at all\n')
            f.write('{"also": "valid"}\n')
        
        loaded = load_decision_records()
        assert len(loaded) == 2
    finally:
        _restore_decisions(backup)


# ── Tests for find_matching_record ──────────────────────────────────────────

def test_find_matching_record_returns_latest():
    """Retorna o record mais recente (último no arquivo) para o input_hash."""
    records = [
        make_test_record(input_hash="sha256:same", kind="early_commitment"),
        make_test_record(input_hash="sha256:other", kind="early_commitment"),
        make_test_record(input_hash="sha256:same", kind="gate"),  # diferente kind
        make_test_record(input_hash="sha256:same", kind="early_commitment"),  # mais recente
    ]
    backup = _write_test_decisions(records)
    try:
        found = find_matching_record("sha256:same", kind="early_commitment")
        assert found is not None
    finally:
        _restore_decisions(backup)


def test_find_matching_record_returns_none_when_not_found():
    """Retorna None quando não há record com o input_hash."""
    records = [make_test_record(input_hash="sha256:other")]
    backup = _write_test_decisions(records)
    try:
        found = find_matching_record("sha256:missing")
        assert found is None
    finally:
        _restore_decisions(backup)


def test_find_matching_record_filters_by_kind():
    """Filtra por kind quando especificado."""
    records = [
        make_test_record(input_hash="sha256:same", kind="early_commitment"),
        make_test_record(input_hash="sha256:same", kind="gate"),
    ]
    backup = _write_test_decisions(records)
    try:
        found = find_matching_record("sha256:same", kind="gate")
        assert found is not None
        assert found["kind"] == "gate"
        
        found = find_matching_record("sha256:same", kind="early_commitment")
        assert found is not None
        assert found["kind"] == "early_commitment"
    finally:
        _restore_decisions(backup)


# ── Tests for attempt_replay ────────────────────────────────────────────────

def test_attempt_replay_returns_none_when_no_record():
    """Retorna None quando não há record correspondente."""
    backup = _write_test_decisions([])
    try:
        result = attempt_replay("sha256:missing")
        assert result is None
    finally:
        _restore_decisions(backup)


def test_attempt_replay_returns_none_when_not_replayable_missing_policy_version():
    """Retorna None quando record não tem policy_version no config."""
    record = make_test_record(config_extra={"policy_version": None})
    backup = _write_test_decisions([record])
    try:
        result = attempt_replay(record["input_hash"])
        assert result is None
    finally:
        _restore_decisions(backup)


def test_attempt_replay_returns_none_when_not_replayable_missing_thresholds_hash():
    """Retorna None quando record não tem thresholds_hash no config."""
    record = make_test_record(config_extra={"thresholds_hash": None})
    backup = _write_test_decisions([record])
    try:
        result = attempt_replay(record["input_hash"])
        assert result is None
    finally:
        _restore_decisions(backup)


def test_attempt_replay_returns_none_when_not_replayable_missing_statechart_to():
    """Retorna None quando record não tem statechart.to."""
    record = make_test_record(statechart_to="")
    backup = _write_test_decisions([record])
    try:
        result = attempt_replay(record["input_hash"])
        assert result is None
    finally:
        _restore_decisions(backup)


def test_attempt_replay_returns_mismatch_when_input_hash_differs():
    """Retorna replay=False com reason=input_hash_mismatch quando hashes divergem."""
    record = make_test_record(input_hash="sha256:original")
    backup = _write_test_decisions([record])
    try:
        # Tenta replay com hash diferente
        result = attempt_replay("sha256:different")
        assert result is not None
        assert result["replayed"] is False
        assert result["reason"] == "input_hash_mismatch"
        assert result["verification"]["input_hash_match"] is False
    finally:
        _restore_decisions(backup)


def test_attempt_replay_success():
    """Replay bem-sucedido retorna decision reproduzida e verification ok."""
    record = make_test_record(
        input_hash="sha256:test123",
        automation="AUTO",
        policy_version="1.0.0",
        thresholds_hash="sha256:abc123",
        statechart_to="active",
    )
    backup = _write_test_decisions([record])
    try:
        result = attempt_replay("sha256:test123")
        assert result is not None
        assert result["replayed"] is True
        assert "decision" in result
        assert "verification" in result
        assert result["verification"]["ok"] is True
        assert result["verification"]["input_hash_match"] is True
        assert result["verification"]["decision_match"] is True
    finally:
        _restore_decisions(backup)


def test_attempt_replay_respects_kind_filter():
    """Replay só encontra records do kind especificado."""
    records = [
        make_test_record(input_hash="sha256:same", kind="early_commitment", automation="AUTO"),
        make_test_record(input_hash="sha256:same", kind="gate", automation="HUMAN_REQUIRED"),
    ]
    backup = _write_test_decisions(records)
    try:
        # Busca early_commitment
        result = attempt_replay("sha256:same", kind="early_commitment")
        assert result is not None
        assert result["replayed"] is True
        
        # Busca gate (não deve encontrar early_commitment)
        result = attempt_replay("sha256:same", kind="gate")
        assert result is not None
        assert result["replayed"] is True
    finally:
        _restore_decisions(backup)


# ── Tests for log_replay_attempt ────────────────────────────────────────────

def test_log_replay_attempt_writes_event(tmp_path):
    """log_replay_attempt escreve evento no replay.jsonl."""
    import llc_replay.verify as verify_mod

    test_log_path = tmp_path / "replay.jsonl"

    def patched_log_replay_attempt(input_hash, result, kind="early_commitment"):
        from datetime import datetime
        event = {
            "timestamp": datetime.now().isoformat(),
            "event": "replay_attempt",
            "input_hash": input_hash,
            "kind": kind,
            "replayed": result["replayed"] if result else False,
            "reason": result.get("reason") if result else "no_record",
            "verification_ok": result["verification"]["ok"] if result and result.get("verification") else False,
        }
        test_log_path.parent.mkdir(exist_ok=True)
        with open(test_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    original = verify_mod.log_replay_attempt
    verify_mod.log_replay_attempt = patched_log_replay_attempt
    try:
        verify_mod.log_replay_attempt("sha256:test", {"replayed": True, "verification": {"ok": True}})
        verify_mod.log_replay_attempt("sha256:test2", None)

        assert test_log_path.exists()
        lines = test_log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        event1 = json.loads(lines[0])
        assert event1["replayed"] is True
        assert event1["verification_ok"] is True

        event2 = json.loads(lines[1])
        assert event2["replayed"] is False
        assert event2["reason"] == "no_record"
    finally:
        verify_mod.log_replay_attempt = original


def test_log_replay_attempt_uses_trace_directory(monkeypatch, tmp_path):
    trace_dir = tmp_path / "trace"
    isolated_cwd = tmp_path / "cwd"
    isolated_cwd.mkdir()
    monkeypatch.chdir(isolated_cwd)
    monkeypatch.setenv("LLC_TRACE_DIR", str(trace_dir))

    log_replay_attempt("sha256:isolated", None)

    assert (trace_dir / "replay.jsonl").is_file()


# ── Integration Tests ────────────────────────────────────────────────────────

def test_replay_integration_with_classifier():
    """Teste de integração: classifier usa replay quando input_hash bate."""
    from llc2.classifier import classify_task_v2
    from llc2.jev_adapter import FakeJevTransport
    
    # Cria record com mesmo input_hash que o classifier vai gerar
    task = "Criar endpoint de usuarios"
    input_hash_value = canonical_hash({"task": task})
    
    record = make_test_record(
        input_hash=input_hash_value,
        automation="AUTO",
        policy_version="1.0.0",
        thresholds_hash="sha256:abc123",
        statechart_to="active",
    )
    backup = _write_test_decisions([record])
    
    try:
        # Transport que retorna classificação alta
        transport = _choice_transport("crud_endpoint", 0.95)
        
        # Deve usar replay e não chamar Jev
        result = classify_task_v2(task, client=None, _transport=transport)
        
        assert result["type"] == "crud_endpoint"
        assert result["replayed"] is True
        assert result["input_hash"] == input_hash_value
    finally:
        _restore_decisions(backup)


def test_replay_fallback_to_jev_when_no_record():
    """Quando não há record, classifier chama Jev normalmente."""
    from llc2.classifier import classify_task_v2
    from llc2.jev_adapter import FakeJevTransport
    
    task = "Tarefa totalmente nova que nao tem cache"
    backup = _write_test_decisions([])
    
    try:
        transport = _choice_transport("ui_component", 0.88)
        result = classify_task_v2(task, client=None, _transport=transport)
        
        assert result["type"] == "ui_component"
        assert result["replayed"] is False
    finally:
        _restore_decisions(backup)


def test_replay_fallback_to_jev_when_hash_mismatch():
    """Quando input_hash difere, classifier chama Jev (não usa replay inválido)."""
    from llc2.classifier import classify_task_v2
    from llc2.jev_adapter import FakeJevTransport
    
    # Record com hash diferente
    record = make_test_record(input_hash="sha256:oldhash")
    backup = _write_test_decisions([record])
    
    try:
        task = "Criar endpoint"
        transport = _choice_transport("crud_endpoint", 0.92)
        result = classify_task_v2(task, client=None, _transport=transport)
        
        assert result["type"] == "crud_endpoint"
        assert result["replayed"] is False
    finally:
        _restore_decisions(backup)


def test_replay_with_different_automation_levels():
    """Replay preserva automation level do record original."""
    for automation in ["AUTO", "REVIEW_REQUIRED", "HUMAN_REQUIRED", "AUTO_AUDIT"]:
        input_hash = f"sha256:test_{automation.lower()}"
        record = make_test_record(
            input_hash=input_hash,
            automation=automation,
            policy_version="1.0.0",
            thresholds_hash="sha256:abc123",
            statechart_to="active",
        )
        backup = _write_test_decisions([record])
        
        try:
            result = attempt_replay(input_hash)
            assert result is not None
            assert result["replayed"] is True
            assert result["decision"].automation.value == automation
        finally:
            _restore_decisions(backup)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])