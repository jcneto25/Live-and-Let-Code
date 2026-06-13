#!/usr/bin/env python3
"""
LLC Task Classifier — Early Commitment engine.

Classifies a task description into one of 4 types using the LLM.
The classification collapses the search space BEFORE execution,
preventing the agent from exploring dead-end paths.

Taxonomy (Pareto: 4 types cover ~80% of repeatable tasks):
- crud_endpoint: API endpoint CRUD operations
- ui_component: UI component creation/modification
- validation_rule: Schema/field/input validation
- test_write: Test writing (unit, integration, E2E)
"""

import subprocess
import sys
import shutil
from typing import Optional


TASK_TYPES = {
    "crud_endpoint": "criar/alterar/deletar/listar endpoints de API",
    "ui_component": "criar/alterar componentes de interface (form, tabela, modal)",
    "validation_rule": "adicionar/alterar validacao em schema, campo ou sanitizacao",
    "test_write": "escrever testes unitarios, integracao ou E2E",
}

CONFIDENCE_THRESHOLD = 0.80


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


def classify_task(task_description, client=None):
    """Classifica uma task. Retorna dict ou None se falhar."""
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

    import re
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
