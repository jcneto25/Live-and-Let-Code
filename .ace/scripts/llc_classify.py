#!/usr/bin/env python3
"""
LLC Task Classifier — Early Commitment engine.

Classifies a task description into one of 4 types using the LLM.
The classification collapses the search space BEFORE execution,
preventing the agent from exploring dead-end paths.

Fase 1 (LLC 2.0): Jev Choice + Decision Policy.
- Rótulo SEMPRE preservado (nunca descartado por baixa confiança)
- Retorna campo `routing`: AUTO | REVIEW_REQUIRED | HUMAN_REQUIRED
- Integração com llc_trace para Decision Records versionados

Taxonomy (Pareto: 4 types cover ~80% of repeatable tasks):
- crud_endpoint: API endpoint CRUD operations
- ui_component: UI component creation/modification
- validation_rule: Schema/field/input validation
- test_write: Test writing (unit, integration, E2E)
"""

import os
import subprocess
import sys
import shutil
import re
from typing import Any, Optional


TASK_TYPES = {
    "crud_endpoint": "criar/alterar/deletar/listar endpoints de API",
    "ui_component": "criar/alterar componentes de interface (form, tabela, modal)",
    "validation_rule": "adicionar/alterar validacao em schema, campo ou sanitizacao",
    "test_write": "escrever testes unitarios, integracao ou E2E",
}

CONFIDENCE_THRESHOLD = 0.80

# ── Feature flag LLC 2.0 ──────────────────────────────────────────────────
_LLC2_AVAILABLE = False
try:
    from llc2.classifier import classify_task_v2
    _LLC2_AVAILABLE = True
except ImportError:
    classify_task_v2 = None  # type: ignore[misc,assignment]

_USE_LLC2 = _LLC2_AVAILABLE and os.environ.get("LLC2_CLASSIFY", "1").strip() not in (
    "0", "", "false", "no",
)


def detect_llm_client():
    """Detecta cliente CLI disponivel para o prompt de classificacao."""
    for client in ["claude", "opencode", "codex", "cursor"]:
        if shutil.which(client):
            return client
    return None


def build_classify_prompt(task_description):
    """Monta prompt de classificacao (~150 tokens)."""
    categories = "\n".join(
        f"- {t}: {d}" for t, d in TASK_TYPES.items()
    )
    return f"""Classifique a tarefa abaixo em uma destas 4 categorias.
Se a tarefa envolver multiplos aspectos (ex: "Criar endpoint com validacao"),
escolha o tipo que representa a MAIOR PARTE do esforco de codificacao.
Ex: "Criar endpoint de usuario com validacao de email" -> crud_endpoint

Categorias:
{categories}

Se nao se encaixar em nenhuma, retorne type="unknown".

Tarefa: {task_description}

Responda APENAS com XML:
<task_classification><type>...</type><confidence>0.XX</confidence>
<reasoning>...</reasoning></task_classification>"""


def _classify_task_legacy(task_description, client=None):
    """Classificador legado (LLC 1.x). Retorna dict ou None se falhar."""
    if client is None:
        client = detect_llm_client()

    prompt = build_classify_prompt(task_description)

    if client:
        result = subprocess.run(
            [client, "--prompt", prompt],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
    else:
        return None

    type_match = re.search(r"<type>(.*?)</type>", output)
    confidence_match = re.search(r"<confidence>(.*?)</confidence>", output)
    reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", output)

    if not type_match:
        return None

    task_type = type_match.group(1).strip()
    if task_type == "unknown" or task_type not in TASK_TYPES:
        return None

    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
    reasoning = reasoning_match.group(1) if reasoning_match else ""

    if confidence < CONFIDENCE_THRESHOLD:
        return None

    return {
        "type": task_type,
        "confidence": confidence,
        "reasoning": reasoning,
    }


def classify_task(task_description, client=None):
    """Classifica uma task.

    Fase 1 (LLC 2.0): quando llc2 está disponível e LLC2_CLASSIFY != 0,
    usa Jev Choice + Decision Policy. O rótulo é SEMPRE preservado e o
    campo `routing` indica o nível de automação.

    Fallback legado: quando llc2 indisponível ou LLC2_CLASSIFY=0,
    comportamento LLC 1.x (pode retornar None).
    """
    if _USE_LLC2 and classify_task_v2 is not None:
        return classify_task_v2(task_description, client=client)
    return _classify_task_legacy(task_description, client=client)
