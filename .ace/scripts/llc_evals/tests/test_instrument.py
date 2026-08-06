"""Testes para llc_evals.instrument — RF-EF1.1/1.2/1.3/1.4/1.6 (PRP-EVALS-F1).

Captura de tokens/custo em 3 níveis com fallback; tool-agnostic (P5); o bloco
<eval_metrics> é produzido por instrument.build_eval_metrics() mas escrito apenas
por finalize_session.py (escritor único — RF-EF1.4). instrument.py nunca grava
em .ace/sessions/.
"""
import ast
from pathlib import Path

import pytest

from llc_evals import instrument


def test_level1_native_log(tmp_path):
    """RF-EF1.1: log claude nativo (level_1) → source/precisão e tokens totais."""
    (tmp_path / "native.jsonl").write_text(
        '{"message":{"usage":{"input_tokens":10000,"output_tokens":3000}}}\n'
        '{"message":{"usage":{"input_tokens":2000,"output_tokens":500}}}\n',
        encoding="utf-8",
    )
    m = instrument.capture_tokens(claude_dir=tmp_path)
    assert m["source"] == "level_1"
    assert m["precision"] == "exact"
    assert m["tokens_in"] == 12000
    assert m["tokens_out"] == 3500
    assert m["total_tokens"] == 15500


def test_level2_structured_usage():
    """RF-EF1.2: sem log mas com bloco usage estruturado → level_2."""
    output = ('{"choices":[{"text":"ok"}],'
              '"usage":{"prompt_tokens":12000,"completion_tokens":3500}}')
    m = instrument.capture_tokens(output_text=output)
    assert m["source"] == "level_2"
    assert m["precision"] == "exact"
    assert m["tokens_in"] == 12000
    assert m["tokens_out"] == 3500
    assert m["total_tokens"] == 15500


def test_level2_usage_can_be_inside_content():
    """Nível 2 também detecta bloco usage embutido em qualquer texto."""
    output = ('texto... "usage": {"prompt_tokens": 100, "completion_tokens": 50} fim')
    m = instrument.capture_tokens(output_text=output)
    assert m["source"] == "level_2"
    assert m["total_tokens"] == 150


def test_level3_estimate_fallback():
    """RF-EF1.3: sem log nem usage block → level_3 (estimativa)."""
    m = instrument.capture_tokens(input_text="palavra " * 1000)
    assert m["source"] == "level_3"
    assert m["precision"] == "estimated"  # RF-EF1.6
    assert m["total_tokens"] > 0
    assert m["tokens_in"] >= 0


def test_level3_does_not_require_tiktoken(tmp_path):
    """Nível 3 degrada para heurística se tiktoken indisponível (still level_3)."""
    m = instrument.capture_tokens(input_text="uma frase de teste " * 50)
    assert m["source"] == "level_3"
    assert m["total_tokens"] > 0


def test_sources_preference_order(tmp_path):
    """Log nativo tem prioridade sobre usage block (level_1 > level_2 > level_3)."""
    (tmp_path / "native.jsonl").write_text(
        '{"message":{"usage":{"input_tokens":100,"output_tokens":100}}}\n',
        encoding="utf-8",
    )
    output = '{"usage":{"prompt_tokens":1,"completion_tokens":1}}'
    m = instrument.capture_tokens(claude_dir=tmp_path, output_text=output)
    assert m["source"] == "level_1"  # level_1 vence


def test_build_eval_metrics_well_formed():
    """RF-EF1.4: bloco <eval_metrics> bem-formado (não escreve em disco)."""
    metrics = {
        "tokens_in": 12000, "tokens_out": 3500, "total_tokens": 15500,
        "cost_usd": 0.08, "duration_s": 45, "retries": 0,
        "source": "level_1", "precision": "exact",
    }
    block = instrument.build_eval_metrics(
        metrics, step="5", timestamp="2026-08-05T10:00:00")
    assert "<eval_metrics" in block
    assert 'timestamp="2026-08-05T10:00:00"' in block
    assert 'step: "5"' in block
    assert "total_tokens: 15500" in block


def test_instrument_never_writes_sessions():
    """RF-EF1.4: AST de instrument.py sem open(...'w'/'a') nem write/write_text."""
    src = Path(instrument.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "open":
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                    assert "a" not in mode and "w" not in mode, \
                        "instrument.py não pode abrir arquivos para escrita"
            if isinstance(fn, ast.Attribute) and fn.attr in ("write_text", "write", "append"):
                raise AssertionError("instrument.py não pode escrever arquivos")
