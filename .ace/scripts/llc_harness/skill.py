#!/usr/bin/env python3
"""Skill loading (R4: progressive disclosure) and agent convention extraction."""

import re
import sys
from pathlib import Path

from llc_steps import normalize_step

from .common import AGENTS_FILE, SKILLS_DIR


def load_agents_conventions():
    """Carrega apenas o Document Index do AGENTS.md, nao o arquivo inteiro (R4).
    O agente usa o indice comprimido para decidir quais arquivos carregar sob demanda."""
    if not AGENTS_FILE.exists():
        return ""

    content = AGENTS_FILE.read_text(encoding="utf-8")
    # Extrai apenas a secao Documentation Index (compacta, ~400 tokens)
    match = re.search(
        r"### Documentation Index \(Compressed\)(.*?)(?=\n## |\n---\n## |\Z)",
        content,
        re.DOTALL,
    )
    if match:
        index_section = match.group(0)
        return (
            "---\n# CONVENTIONS (Document Index only — progressive disclosure)\n---\n\n"
            + index_section
            + "\n\n---\n# TASK\n---\n\n"
        )
    # Fallback: carrega so as primeiras 50 linhas (cabecalho + zonas)
    lines = content.split("\n")[:50]
    return (
        "---\n# CONVENTIONS (header only)\n---\n\n"
        + "\n".join(lines)
        + "\n\n---\n# TASK\n---\n\n"
    )


def skill_load(step, context_seed=None, task=None):
    """Carrega skill + convencoes minimal + context_seed. Retorna prompt montado.

    Resolucao deterministica via llc_steps.REGISTRY (sem glob/ambiguidade):
    cada StepSpec aponta para um skill_file exato. Step sem skill_file -> erro.
    """
    spec = normalize_step(step)
    if not spec.skill_file:
        print(f"❌ Step {spec.id} ({spec.name}) nao tem skill associada.")
        sys.exit(1)
    skill_file = SKILLS_DIR / f"{spec.skill_file}.md"
    if not skill_file.exists():
        print(f"❌ Skill nao encontrada: {skill_file} (step {spec.id})")
        sys.exit(1)

    conventions = load_agents_conventions()
    skill = skill_file.read_text(encoding="utf-8")

    prompt = conventions + skill

    if context_seed:
        prompt += f"\n\n---\n# CONTEXT (sessao anterior)\n---\n\n{context_seed}"

    if task:
        prompt += f"\n\n---\n# TASK\n---\n\n{task}"

    prompt += "\n\n---\n# FINALIZACAO\n---\n\n"
    prompt += (
        "Ao concluir este step, gere um context_seed no formato ACE de 4 campos:\n"
    )
    prompt += "state: [acoes concluidas, arquivos alterados]\n"
    prompt += "pending: [tarefas incompletas]\n"
    prompt += "blockers: [impedimentos ativos]\n"
    prompt += "next_action: [proximo passo recomendado]\n"

    return str(skill_file), prompt
