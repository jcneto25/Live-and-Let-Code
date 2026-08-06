#!/usr/bin/env python3
"""finalize_session — geração e gravação do context_seed."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import logger


def build_context_seed(
    actions: list[dict],
    learnings: list[dict],
    blockers: list[dict],
    gate_present: bool,
    agent_seed: Optional[str] = None,
) -> str:
    """Constrói o context_seed no schema de 4 campos OBRIGATÓRIOS."""
    if agent_seed:
        return agent_seed

    state_parts = []
    if actions:
        last_actions = actions[-5:]
        for a in last_actions:
            a_type = a["attrs"].get("type", "?")
            desc_match = re.search(r'<description>(.*?)</description>', a["content"])
            file_match = re.search(r'<file_delta>(.*?)</file_delta>', a["content"])
            file_delta = file_match.group(1).strip() if file_match else ""
            description = desc_match.group(1).strip() if desc_match else ""
            if description:
                state_parts.append(f"[{a_type}] {description}")
    state = "; ".join(state_parts) if state_parts else "sessão concluída"

    pending_parts = []
    unresolved = [b for b in blockers if b["attrs"].get("resolved", "false").lower() == "false"]
    for b in unresolved[:3]:
        pending_parts.append(b["content"].strip())
    if not pending_parts:
        pending_parts.append("nenhuma pendência identificada")
    pending = "; ".join(pending_parts)

    if unresolved:
        blocker_texts = [b["content"].strip() for b in unresolved[:3]]
        blockers_str = "; ".join(blocker_texts)
    else:
        blockers_str = "nenhum ativo"

    if unresolved:
        next_action = f"resolver blocker: {unresolved[0]['content'].strip()}"
    elif not gate_present:
        next_action = "validar etapa atual (gate pendente)"
    else:
        next_action = "prosseguir para a próxima etapa"

    return f"state: {state}\npending: {pending}\nblockers: {blockers_str}\nnext_action: {next_action}"


def write_context_seed(session_file: Path, context_seed: str, dry_run: bool = False):
    """Substitui APENAS o placeholder de context_seed na seção ## Encerramento.

    Não modifica o <context_seed> da seção ## Contexto (que é da sessão anterior).
    """
    content = session_file.read_text(encoding='utf-8')

    placeholder = "state: [preencher no encerramento]\npending: [preencher no encerramento]\nblockers: [preencher no encerramento]\nnext_action: [preencher no encerramento]"

    if placeholder in content:
        if not dry_run:
            content = content.replace(placeholder, context_seed)
            session_file.write_text(content, encoding='utf-8')
        logger.info("✅ context_seed gravado na seção Encerramento")
    else:
        logger.warning("⚠️  Placeholder de context_seed não encontrado — appendando ao final")
        if not dry_run:
            with open(session_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## Contexto para Próxima Sessão\n\n<context_seed>\n{context_seed}\n</context_seed>\n")


def update_session_status(session_file: Path, status: str, dry_run: bool = False):
    """Atualiza o campo `status:` (quoted) no frontmatter do arquivo de sessão."""
    content = session_file.read_text(encoding='utf-8')
    new_content, n = re.subn(r'(status:\s*)"[^"]*"', rf'\g<1>"{status}"', content, count=1)
    if n == 0:
        logger.warning(f"⚠️  Campo status (quoted) não encontrado no frontmatter de {session_file.name}")
        return
    if not dry_run:
        session_file.write_text(new_content, encoding='utf-8')
    logger.info(f"✅ status do arquivo da sessão atualizado: {status}")


def append_eval_metrics(session_file: Path, step: Optional[str] = None,
                        dry_run: bool = False) -> bool:
    """Append do bloco `<eval_metrics>` na sessão (RF-EF1.4 / GOV-003/R8).

    Escritor único = `finalize_session` (este módulo é mutador sancionado).
    `instrument.py` apenas produz o bloco — NUNCA grava na sessão. Best-effort:
    se `llc_evals` estiver indisponível, loga e retorna False (sem quebrar o
    finalize). Nível 3 (estimativa) usa o corpo da sessão como base (P5/EF1.6).
    """
    try:
        from llc_evals import instrument
    except Exception:  # noqa: BLE001
        logger.info("ℹ️  <eval_metrics> ignorado (llc_evals indisponível)")
        return False
    try:
        body = session_file.read_text(encoding="utf-8") if session_file.exists() else ""
        metrics = instrument.capture_tokens(input_text=body)  # level_3 fallback
        block = instrument.build_eval_metrics(
            metrics,
            step=step or "",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
    except Exception as exc:  # noqa: BLE001 — degradação graciosa
        logger.warning(f"⚠️  <eval_metrics> não gerado: {exc}")
        return False
    if not dry_run:
        with open(session_file, "a", encoding="utf-8") as fh:
            fh.write("\n" + block + "\n")
    logger.info("✅ <eval_metrics> appendado na sessão (append-only)")
    return True
