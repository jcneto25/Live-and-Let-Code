"""
llc_delta — modulo de suporte ao fluxo delta (mudancas em sistema existente).

Responsabilidades:
- Ler e interpretar DELTA_REPORT.md
- Determinar quais steps executar vs pular
- Gerar skip notes automaticamente
- Integrar com pipeline_run para modo delta
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Constants ──

DELTA_REPORT_PATH = Path("docs/planning/DELTA_REPORT.md")
SKIP_NOTES_DIR = Path("docs/delta/skip-notes")


# ── Parse DELTA_REPORT.md ──


def delta_report_exists() -> bool:
    return DELTA_REPORT_PATH.exists()


def parse_delta_report() -> dict | None:
    """Le o DELTA_REPORT.md e extrai a secao de plano de execucao.

    Retorna dict com:
      - change_type: "major" | "minor"
      - execute_steps: lista de step_ids (strings) a executar
      - skip_steps: lista de {step_id, reason, artifacts_reused}
      - iteration: string "vN" ou None
      - affected_prps: lista de PRP ids
      - new_prps: lista de PRP-N ids
    Retorna None se o arquivo nao existir ou nao for parseavel.
    """
    if not DELTA_REPORT_PATH.exists():
        return None

    content = DELTA_REPORT_PATH.read_text(encoding="utf-8")

    result = {
        "change_type": "unknown",
        "execute_steps": [],
        "skip_steps": [],
        "iteration": None,
        "affected_prps": [],
        "new_prps": [],
    }

    # Extrai iteracao do §1
    m = re.search(r"Iteracao proposta\s*\|\s*`(v[\d.]+)`", content)
    if m:
        result["iteration"] = m.group(1)

    # Extrai classificacao
    m = re.search(r"Classificacao\s*\|\s*`(\w+)`", content)
    if m:
        result["change_type"] = m.group(1).lower()

    # Extrai steps a executar (§5.1)
    in_execute = False
    in_skip = False
    for line in content.split("\n"):
        stripped = line.strip()

        if "Steps a Executar" in stripped:
            in_execute = True
            in_skip = False
            continue
        if "Steps a Pular" in stripped:
            in_execute = False
            in_skip = True
            # Pula o cabecalho da tabela (| Step | ... |)
            continue
        if in_execute and stripped.startswith("|") and not stripped.startswith("|---"):
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if parts and len(parts) >= 1:
                step_id = parts[0].strip()
                if step_id and not step_id.startswith("Step"):
                    result["execute_steps"].append(step_id)

        if in_skip and stripped.startswith("|") and not stripped.startswith("|---"):
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if parts and len(parts) >= 2:
                skip_entry = {
                    "step_id": parts[0].strip(),
                    "reason": parts[1].strip(),
                    "artifacts_reused": parts[2].strip() if len(parts) > 2 else "",
                }
                result["skip_steps"].append(skip_entry)
                # Muda in_skip para False apos ler a linha (so espera uma linha da tabela)
                # Na verdade, a tabela tem multiplas linhas, entao mantemos True

    # Extrai PRPs afetados (§3.2)
    in_affected = False
    for line in content.split("\n"):
        if "PRPs Existentes com Alteracao (PRP-A)" in line:
            in_affected = True
            continue
        if in_affected and line.startswith("|") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if parts and len(parts) >= 1 and parts[0].startswith("PRP-"):
                result["affected_prps"].append(parts[0])
        elif in_affected and not line.startswith("|"):
            in_affected = False

    # Extrai novos PRPs (§4)
    in_new = False
    for line in content.split("\n"):
        if "Novos PRPs Necessarios (PRP-N)" in line:
            in_new = True
            continue
        if in_new and line.startswith("|") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if parts and len(parts) >= 1 and parts[0].startswith("PRP-"):
                result["new_prps"].append(parts[0])
        elif in_new and not line.startswith("|"):
            in_new = False

    return result


# ── Smart Skip ──


def is_step_skipped(step_id: str, delta_plan: dict | None) -> bool:
    """Verifica se um step deve ser pulado no modo delta."""
    if delta_plan is None:
        return False
    for skip in delta_plan.get("skip_steps", []):
        if skip["step_id"] == step_id:
            return True
    return False


def get_skip_reason(step_id: str, step_name: str, delta_plan: dict | None) -> str | None:
    """Retorna a justificativa de skip para um step, ou None se nao for skip."""
    if delta_plan is None:
        return None
    for skip in delta_plan.get("skip_steps", []):
        if skip["step_id"] == step_id:
            return skip.get("reason", "Nao informado")
    return None


def generate_skip_note(step_id: str, step_name: str, reason: str,
                       iteration: str | None = None) -> Path:
    """Gera um skip note para o step e retorna o caminho do arquivo."""
    SKIP_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_file = SKIP_NOTES_DIR / f"step-{step_id}.md"

    content = [
        f"# Skip Note: Step {step_id} — {step_name}",
        "",
        f"**Decisao:** Step pulado conforme DELTA_REPORT.md",
        f"**Justificativa:** {reason}",
        "",
    ]
    if iteration:
        content.append(f"**Iteracao:** {iteration}")
    content.append("")
    content.append(
        "**Gate:** ✅ Auto-aprovado via Smart Skip "
        "(reaproveitando artefatos da versao anterior)"
    )
    content.append("")

    note_file.write_text("\n".join(content), encoding="utf-8")
    return note_file


# ── Integration with pipeline ──


def get_delta_steps(delta_plan: dict | None) -> list[str]:
    """Retorna a lista de steps a executar no modo delta.

    Inclui steps de analise (0.2, 0.3) se DELTA_REPORT.md ainda nao existir,
    mais os steps listados em execute_steps do relatorio.
    """
    steps = []

    if delta_plan is None or not delta_report_exists():
        # Delta ainda nao iniciado — precisa executar Δ.0 primeiro
        steps.append("0.2")  # Delta Impact Analysis
        steps.append("0.3")  # Delta Grill Me
    else:
        # Delta ja analisado — executar steps planejados
        for step_id in delta_plan.get("execute_steps", []):
            steps.append(step_id)

    return steps
