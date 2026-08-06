"""llc_evals.ingest — conector sessão ACE → BaselineManager (P1 pos-roadmap).

Fechava o elo que faltava na cadeia Evals: `finalize_session.py` append
`<eval_metrics>` nas sessões (RF-EF1.4), mas **ninguém lia esse bloco** — o
`BaselineManager.record_run()` (EVALS-F4) não tinha callers. Este módulo:

- `parse_eval_metrics(content)` — extrai blocos `<eval_metrics>` das sessões
- `quality_from_gate(content)` — quality score determinístico a partir do
  `<gate_result>` da sessão (approved → 100.0, rejected → 0.0)
- `ingest_sessions()` — varre `.ace/sessions/*.md`, alimenta `record_run()`
  com idempotência (estado em `.ace/evals/state.yaml`) e suporte a `--dry-run`

Read-only sobre `.ace/sessions/` (P1/RF-W1A.15): apenas lê os arquivos de
sessão; grava exclusivamente em `.ace/evals/` (baselines + estado de ingest).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from llc_evals.aggregate import BaselineManager

# Bloco `<eval_metrics timestamp="...">...</eval_metrics>` (RF-EF1.4)
_BLOCK_RE = re.compile(
    r"<eval_metrics[^>]*>(.*?)</eval_metrics>", re.DOTALL
)
# timestamp no opening tag: `<eval_metrics timestamp="...">`
_OPEN_TAG_TS_RE = re.compile(r"<eval_metrics[^>]*timestamp=\"([^\"]*)\"")
# Campo `name: "value"` ou `name: value` dentro do bloco
_FIELD_RE = re.compile(
    r"^\s*([a-z_]+):\s*(?:\"([^\"]*)\"|(\S+))\s*$", re.MULTILINE
)
# `<gate_result ... decision="approved|rejected" ...>`
_GATE_DECISION_RE = re.compile(
    r'<gate_result[^>]*\bdecision="(approved|rejected)"'
)

# Nível de precisão → peso no bucket (mesma semântica do aggregate)
_PRECISION_ORDER = {"level_1": 1, "level_2": 2, "level_3": 3}


def parse_eval_metrics(content: str) -> list[dict]:
    """Extrai blocos `<eval_metrics>` do conteúdo de uma sessão.

    Retorna lista de dicts com step/tokens/source/precision. Comentários HTML
    (`<!-- ... -->`) são ignorados (placeholders não são dados reais).
    """
    # remove comentários HTML para ignorar placeholders de template
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    blocks: list[dict] = []
    for match in _BLOCK_RE.finditer(content):
        fields: dict = {}
        for f in _FIELD_RE.finditer(match.group(1)):
            name, quoted, bare = f.group(1), f.group(2), f.group(3)
            raw = quoted if quoted is not None else bare
            fields[name] = raw
        if not fields:
            continue
        # timestamp vive no opening tag (não no corpo) — captura explícita
        # para a chave de idempotência ser realmente sessão+timestamp
        ts = _OPEN_TAG_TS_RE.search(match.group(0))
        if ts:
            fields["timestamp"] = ts.group(1)
        blocks.append(_coerce(fields))
    return blocks


def _coerce(fields: dict) -> dict:
    """Converte campos numéricos para int/float (tokens, custo, retries)."""
    for key in ("tokens_in", "tokens_out", "total_tokens", "retries",
                "duration_s"):
        if key in fields:
            try:
                fields[key] = int(float(fields[key]))
            except (ValueError, TypeError):
                pass
    for key in ("cost_usd",):
        if key in fields:
            try:
                fields[key] = float(fields[key])
            except (ValueError, TypeError):
                pass
    return fields


def quality_from_gate(content: str) -> float | None:
    """Quality score determinístico pelo gate da sessão (ADR-0005 §2.3).

    approved → 100.0 · rejected → 0.0 · sem gate → None (default no ingest).
    É o sinal de qualidade disponível de forma offline/determinística — o
    DocJudge (EVALS-F3) pode substituí-lo quando executado com LLM.

    Comentários HTML (`<!-- <gate_result ...> -->`) são ignorados: placeholders
    de template NÃO contam como gate real (fix review — evita 100.0 falso).
    """
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    m = _GATE_DECISION_RE.search(content)
    if not m:
        return None
    return 100.0 if m.group(1) == "approved" else 0.0


def ingest_sessions(
    *,
    sessions_dir: Path | str,
    baselines_dir: Path | str,
    state_path: Path | str | None = None,
    default_quality: float = 80.0,
    dry_run: bool = False,
) -> dict:
    """Alimenta `BaselineManager.record_run()` a partir das sessões (P1).

    Para cada sessão `.ace/sessions/*.md`:
      1. parse `<eval_metrics>` (ignora blocos sem step)
      2. quality via `<gate_result>` (fallback: `default_quality`)
      3. `record_run(step_id, quality_score, token_cost, source)`

    Idempotência: cada bloco é identificado pelo `session_id` (sessões ACE são
    imutáveis e cada uma carrega no máximo um bloco `<eval_metrics>`) e o
    estado fica em `state_path` (default `.ace/evals/state.yaml`). Re-execução
    não duplica runs. `dry_run=True` apenas calcula (não grava nada).

    Retorna summary com runs_recorded / blocks_found / errors.
    """
    sessions = Path(sessions_dir)
    baselines = Path(baselines_dir)
    if state_path is None:
        state_path = baselines.parent / "state.yaml"
    state_file = Path(state_path)

    seen: set[str] = set()
    if state_file.exists() and not dry_run:
        try:
            data = yaml.safe_load(state_file.read_text(encoding="utf-8"))
            # migração: chaves antigas eram 'session_id:timestamp' (timestamp
            # vazio); normaliza para session_id puro
            seen = {k.split(":")[0] for k in (data or {}).get("ingested", [])}
        except (yaml.YAMLError, OSError):
            seen = set()

    manager = BaselineManager(baselines)
    summary = {
        "sessions_scanned": 0,
        "blocks_found": 0,
        "runs_recorded": 0,
        "skipped_duplicates": 0,
        "errors": [],
    }

    new_ingested: list[str] = []
    if not sessions.is_dir():
        summary["errors"].append(f"sessions dir não encontrado: {sessions}")
        return summary

    for session_file in sorted(sessions.glob("*.md")):
        summary["sessions_scanned"] += 1
        try:
            content = session_file.read_text(encoding="utf-8")
        except OSError as exc:
            summary["errors"].append(f"{session_file.name}: {exc}")
            continue
        session_id = session_file.stem
        blocks = parse_eval_metrics(content)
        summary["blocks_found"] += len(blocks)

        for block in blocks:
            step = block.get("step")
            if not step:
                summary["errors"].append(
                    f"{session_file.name}: bloco sem step ignorado")
                continue
            key = session_id  # sessões imutáveis → 1 bloco por sessão
            if key in seen:
                summary["skipped_duplicates"] += 1
                continue

            try:
                token_cost = float(block.get("total_tokens", 0.0))
            except (ValueError, TypeError):
                token_cost = 0.0
            if token_cost <= 0:
                summary["errors"].append(
                    f"{session_file.name}: bloco sem total_tokens válido ignorado")
                continue
            source = block.get("source", "level_3")
            if source not in _PRECISION_ORDER:
                summary["errors"].append(
                    f"{session_file.name}: source desconhecido '{source}'")
                continue
            quality = quality_from_gate(content)
            if quality is None:
                quality = float(default_quality)

            if not dry_run:
                manager.record_run(
                    step_id=step,
                    quality_score=quality,
                    token_cost=token_cost,
                    source=source,
                )
            summary["runs_recorded"] += 1
            new_ingested.append(key)

    if not dry_run and new_ingested:
        seen.update(new_ingested)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            yaml.safe_dump({"ingested": sorted(seen)}, sort_keys=True),
            encoding="utf-8",
        )

    summary["new_ingested"] = len(new_ingested)
    summary["total_ingested"] = len(seen)
    return summary
