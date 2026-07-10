#!/usr/bin/env python3
"""Wave execution orchestrator (run_wave)."""

import logging

from .checks import (
    _is_ui_prp,
    _post_wave_check,
    _pre_wave_check,
    _verify_backend_contracts,
)
from .models import PrpInfo
from .parsing import parse_execution_waves, parse_tasks

logger = logging.getLogger(__name__)


def run_wave(
    wave_num: int,
    aggregate: bool = False,
    dry_run: bool = False,
    no_worktree: bool = False,
    auto_approve: bool = False,
) -> bool:
    """Executa uma onda: itera PRPs e abre sessoes.

    Retorna True se todas as sessoes foram bem-sucedidas.
    """
    waves = parse_execution_waves()
    if not waves:
        logger.error("Nenhuma wave encontrada em EXECUTION_WAVES.md.")
        return False

    wave = next((w for w in waves if w.number == wave_num), None)
    if not wave:
        valid = [w.number for w in waves]
        logger.error(f"Wave {wave_num} nao encontrada. Waves disponiveis: {valid}")
        return False

    prps_map = parse_tasks()
    prp_ids = wave.prps if wave.prps else list(prps_map.keys())

    if not prp_ids:
        logger.warning(
            f"Wave {wave_num} nao tem PRPs associados. "
            f"Popule EXECUTION_WAVES.md ou crie PRPs no Step 3."
        )
        return False

    logger.info(f"🚀 Wave {wave_num}: {wave.name or '(sem nome)'}")
    logger.info(f"   PRPs: {len(prp_ids)}")

    if dry_run:
        logger.info("🏁 Modo dry-run — nenhuma sessao sera criada.")
        for prp_id in prp_ids:
            info = prps_map.get(prp_id, PrpInfo(prp_id))
            task_info = f" ({len(info.tasks)} tasks)" if info.tasks else ""
            logger.info(f"   • {prp_id}{task_info}")
            for tid in info.tasks:
                logger.info(f"       ├── {tid}")
        return True

    # Pre-wave validation: build + bootstrap + health (baseline)
    if not _pre_wave_check(dry_run=dry_run, wave_num=wave_num):
        logger.error(
            f"⛔ Wave {wave_num} — pre-wave check FALHOU. Corrija os erros e tente novamente."
        )
        return False

    # Import harness functions only when not dry-run
    try:
        from llc_harness import gate_check, session_end, step_run
    except ImportError as e:
        logger.error(
            f"Erro ao importar llc_harness: {e}\n\n"
            "O comando `wave run` depende dos modulos de orquestracao do harness.\n"
            "Certifique-se de estar executando a partir de .ace/scripts/:\n"
            f"  cd .ace/scripts && python llc.py wave run --wave {wave_num}"
        )
        return False

    if aggregate:
        # Sessao agregada — um unico ciclo para toda a wave
        task_desc = f"Wave {wave_num}: {wave.name or ''}. PRPs: {', '.join(prp_ids)}"
        logger.info(f"📦 Sessao agregada: {task_desc}")

        sid = step_run("11", task=task_desc, wave=wave_num, no_worktree=no_worktree)
        decision = gate_check("11", None, auto_approve=auto_approve)
        session_end(sid, decision, None, step="11")

        if decision != "approved":
            logger.warning(f"⛔ Wave {wave_num} — gate rejeitado.")
            return False
    else:
        # Sessao por PRP — um ciclo para cada PRP
        logger.info(f"📦 Sessoes individuais por PRP ({len(prp_ids)} PRPs)")

        for prp_id in prp_ids:
            info = prps_map.get(prp_id, PrpInfo(prp_id))
            task_desc = f"{prp_id}: {info.name or prp_id}"

            logger.info(f"\n{'─' * 50}")
            logger.info(f"▶  Iniciando {prp_id}")

            # API-first enforcement: verifica contratos de backend antes de PRPs com UI (Trilha B)
            if _is_ui_prp(prp_id, info):
                logger.info(f"   🎨 {prp_id} detectado como Trilha B (UI)")
                if not _verify_backend_contracts(prp_id, info, dry_run=dry_run):
                    logger.error(
                        f"⛔ {prp_id} — contratos de backend não prontos (API-first)."
                    )
                    if auto_approve:
                        logger.info("   Continuando para próximo PRP (auto-approve).")
                    else:
                        logger.info(
                            "   Wave pausada. Implemente os contratos de backend primeiro."
                        )
                        return False

            sid = step_run(
                "11", prp=prp_id, task=task_desc, wave=wave_num, no_worktree=no_worktree
            )
            decision = gate_check("11", None, auto_approve=auto_approve)
            session_end(sid, decision, None, step="11")

            if decision != "approved":
                logger.warning(f"⛔ {prp_id} — gate rejeitado.")
                if auto_approve:
                    logger.info("   Continuando para proximo PRP (auto-approve).")
                else:
                    logger.info(
                        "   Wave pausada. Execute manualmente os PRPs restantes."
                    )
                    return False

    # Post-wave validation: build + bootstrap + health (integridade) + aceite de PRP
    if not _post_wave_check(dry_run=dry_run, wave_num=wave_num, prp_ids=prp_ids):
        logger.error(f"⛔ Wave {wave_num} — pós-onda bloqueada (prp_verify CRITICAL).")
        return False

    logger.info(f"✅ Wave {wave_num} concluida.")
    return True
