#!/usr/bin/env python3
"""Leitura e parsing do DELTA_REPORT.md."""

import re

from .paths import DELTA_REPORT_PATH


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
