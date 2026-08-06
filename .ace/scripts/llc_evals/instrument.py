"""llc_evals.instrument — captura de tokens/custo em 3 níveis (P5, ADR-0005 §2.5).

RF-EF1.1/1.2/1.3/1.4/1.6 (PRP-EVALS-F1): acessa metrics de token de forma
tool-agnostic e com fallback:

  level_1 (exact)   — log nativo (`.claude/`), usage `{input_tokens, output_tokens}`
  level_2 (exact)   — bloco usage estruturado no output (prompt/completion_tokens)
  level_3 (estimated) — estimativa (tiktoken opcional → heurística de palavras)

`build_eval_metrics()` gera o bloco XML `<eval_metrics>` mas NUNCA grava em
`.ace/sessions/` — o escritor único é `finalize_session.py` (RF-EF1.4/GOV-003/R8).
Este módulo é read-only por construção.
"""
from __future__ import annotations

import re
from pathlib import Path

# level 1 — log nativo Claude (`"message":{"usage":{"input_tokens":N,"output_tokens":M}}`)
_LEVEL1_USAGE = re.compile(
    r'"usage"\s*:\s*\{\s*"input_tokens"\s*:\s*(\d+)\s*,\s*'
    r'"output_tokens"\s*:\s*(\d+)'
)
# level 2 — bloco usage estruturado no output (prompt/completion tokens)
_LEVEL2_USAGE = re.compile(
    r'"usage"\s*:\s*\{[^}]*"prompt_tokens"\s*:\s*(\d+)'
    r'[^0-9]*"completion_tokens"\s*:\s*(\d+)'
)

# Modelo de custo aproximado (US$/token) — documentado, não é assert dos RFs.
_USD_PER_TOKEN = 3.0 / 1_000_000


def _level1_claude_usage(claude_dir) -> tuple[int, int] | None:
    """Soma usage nativo Claude nos logs `.jsonl` sob claude_dir (sem write)."""
    if claude_dir is None:
        return None
    d = Path(claude_dir)
    total_in = total_out = 0
    found = False
    if d.is_dir():
        for f in sorted(d.glob("*.jsonl")):
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                m = _LEVEL1_USAGE.search(line)
                if m:
                    found = True
                    total_in += int(m.group(1))
                    total_out += int(m.group(2))
    return (total_in, total_out) if found else None


def _level2_structured_usage(output_text: str | None) -> tuple[int, int] | None:
    """Extrai bloco usage estruturado do output (prompt/completion tokens)."""
    if not output_text:
        return None
    m = _LEVEL2_USAGE.search(output_text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _level3_estimate(input_text: str | None) -> tuple[int, int]:
    """Estimativa (tokens tototais). tiktoken opcional; senão heurística palavras."""
    text = input_text or ""
    total = 0
    try:
        import tiktoken  # nível 3 refinado (optional, N1)
        enc = tiktoken.get_encoding("cl100k_base")
        total = len(enc.encode(text)) if text else 1
    except Exception:  # noqa: BLE001 — degradação graciosa da dependência opcional
        words = len(re.findall(r"\S+", text))
        total = max(int(words * 1.3), 1)
    tokens_out = max(int(total * 0.25), 0)
    tokens_in = total - tokens_out
    return tokens_in, tokens_out


def _metrics(tokens_in: int, tokens_out: int, retries: int,
             source: str, precision: str) -> dict:
    total = tokens_in + tokens_out
    return {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "total_tokens": total,
        "cost_usd": round(total * _USD_PER_TOKEN, 6),
        "duration_s": 0,
        "retries": retries,
        "source": source,
        "precision": precision,
    }


def capture_tokens(*, claude_dir=None, output_text: str | None = None,
                   input_text: str | None = None, retries: int = 0) -> dict:
    """Captura tokens/custo com fallback em 3 níveis (P5). Sempre retorna dict."""
    # level 1 — log nativo (mais preciso)
    l1 = _level1_claude_usage(claude_dir)
    if l1 is not None:
        return _metrics(l1[0], l1[1], retries, "level_1", "exact")
    # level 2 — parsing do bloco usage estruturado
    l2 = _level2_structured_usage(output_text)
    if l2 is not None:
        return _metrics(l2[0], l2[1], retries, "level_2", "exact")
    # level 3 — estimativa (fallback universal)
    tin, tout = _level3_estimate(input_text)
    return _metrics(tin, tout, retries, "level_3", "estimated")


def build_eval_metrics(metrics: dict, *, step, timestamp: str) -> str:
    """Gera o bloco XML `<eval_metrics>` (append-only — NÃO grava em disco)."""
    lines = [
        f'<eval_metrics timestamp="{timestamp}">',
        f'  step: "{step}"',
        f"  tokens_in: {metrics['tokens_in']}",
        f"  tokens_out: {metrics['tokens_out']}",
        f"  total_tokens: {metrics['total_tokens']}",
        f"  cost_usd: {metrics['cost_usd']}",
        f"  duration_s: {metrics['duration_s']}",
        f"  retries: {metrics['retries']}",
        f"  source: \"{metrics['source']}\"",
        f"  precision: \"{metrics['precision']}\"",
        "</eval_metrics>",
    ]
    return "\n".join(lines)
