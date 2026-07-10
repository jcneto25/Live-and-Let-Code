#!/usr/bin/env python3
"""Agent CLI detection, LLM invocation and Early Commitment + Replay orchestration."""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from llc_steps import canonical_id

from .common import SCRIPTS_DIR
from .gates import gate_check

# ── Early Commitment + Replay imports ──
try:
    from llc_classify import classify_task
    from llc_replay import (
        check_target_files_stale,
        deterministic_replay,
        extract_files_from_script,
        find_best_script,
        get_architecture_version,
        is_red_zone,
        log_replay_event,
        preflight_all_steps,
    )

    CLASSIFY_REPLAY_AVAILABLE = True
except ImportError:
    CLASSIFY_REPLAY_AVAILABLE = False


def detect_agent_client():
    """Detecta o cliente de IA CLI via ambiente ou PATH.

    Ordem de precedência:
    1. Variável LLC_AGENT_CLI (ex: LLC_AGENT_CLI=claude)
    2. Primeiro CLI conhecido encontrado no PATH (fallback)

    Nenhum hardcode de flags — todo cliente recebe o prompt via STDIN.
    """
    env_client = os.environ.get("LLC_AGENT_CLI", "").strip()
    if env_client:
        return env_client

    # Fallback: procura CLIs conhecidos no PATH (sem flags — via stdin resolve)
    KNOWN_CLIS = ["claude", "opencode", "codex", "cursor", "windsurf", "copilot"]
    for client in KNOWN_CLIS:
        if shutil.which(client):
            return client
    return None


def agent_invoke(prompt, task_description=None, client=None):
    """Invoca cliente CLI com Early Commitment + Replay."""
    if not CLASSIFY_REPLAY_AVAILABLE:
        return _llm_invoke(prompt, client)

    # 1. Early Commitment: classificar tarefa
    classification = None
    if task_description:
        classification = classify_task(task_description, client)
        if classification:
            log_replay_event(
                "classify",
                None,
                type=classification["type"],
                confidence=classification["confidence"],
            )
            print(
                f"🏷️  Classificado: {classification['type']} "
                f"(confianca: {classification['confidence']:.0%})"
            )

    if classification:
        # 2. Buscar script no cache
        script = find_best_script(classification["type"], task_description)

        if script:
            log_replay_event(
                "replay_hit",
                script["id"],
                type=classification["type"],
                usage_count=script.get("usage_count", 0),
                match_score="computed",
            )

            # 2a. Stale cache check (R3)
            if check_target_files_stale(script.get("target_files", [])):
                log_replay_event("llm_fallback", None, reason="stale_cache")
                print("⚠️  Script obsoleto (arquivos mudaram). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2b. Architecture version check (R3)
            current_arch = get_architecture_version()
            if script.get("architecture_version", "") != current_arch:
                log_replay_event("llm_fallback", None, reason="arch_changed")
                print("⚠️  Script obsoleto (arquitetura mudou). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2c. Zone check (R2)
            target_files = extract_files_from_script(script)
            if any(is_red_zone(Path(f)) for f in target_files):
                print("🔴 Zona VERMELHA detectada. Gate humano necessario.")
                if gate_check(canonical_id(11), script) != "approved":
                    log_replay_event("llm_fallback", None, reason="zone_red_rejected")
                    return _llm_invoke(prompt, client)

            # 2d. Pre-flight (C)
            if not preflight_all_steps(script, {}):
                log_replay_event("llm_fallback", None, reason="preflight_fail")
                return _llm_invoke(prompt, client)

            # 3. REPLAY (R5: rollback integrado)
            print(
                f"⚡ Replay: {classification['type']} "
                f"(script {script['id']}, {script.get('usage_count', 0)} usos)"
            )
            return deterministic_replay(
                script, {}, gate_check, _llm_invoke, prompt, client
            )
        else:
            log_replay_event(
                "replay_miss", None, type=classification["type"], reason="no_cache"
            )

    # 4. Fallback: execucao normal via LLM
    log_replay_event(
        "llm_fallback",
        None,
        reason="no_classify" if not classification else "cache_miss",
    )
    return _llm_invoke(prompt, client)


def _llm_invoke(prompt, client=None):
    """Execucao LLM via pipe STDIN — funciona com qualquer terminal agentico.

    Nao usa flags como --prompt porque cada CLI tem sua propria convencao.
    O prompt e enviado via STDIN (communicate), que todos os CLIs aceitam.

    Se LLC_AGENT_CLI estiver definida, usa esse binario.
    Se nao, detecta o primeiro CLI disponivel no PATH.
    Se nenhum CLI for encontrado, exibe o prompt em modo manual.

    Retorna (output, exit_code, context_seed).
    """
    if client is None:
        client = detect_agent_client()

    if client:
        print(f"🤖 Invocando {client} (prompt via STDIN, {len(prompt)} chars)...")

        process = subprocess.Popen(
            [client],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path.cwd(),
        )

        output = ""
        code = 1
        try:
            output, _ = process.communicate(input=prompt, timeout=600)
            code = process.returncode
            # Print output after execution (modo batch — sem streaming real)
            if output.strip():
                print(output)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            print(f"\n⏰ Timeout (600s).")
            return output or "", 124, None
        except BrokenPipeError:
            print(f"\n⚠️  Pipe quebrado — {client} pode nao aceitar STDIN.")
            return output or "", 1, None

        if code != 0 and not output.strip():
            print(f"\n⚠️  {client} retornou exit code {code} sem output.")
            print(f"   Configure LLC_AGENT_CLI ou execute em modo manual.\n")
            return output, code, None

        # Extrai context_seed do output do agente (G2)
        seed_match = re.search(
            r"state:\s*(.*?)\n\s*pending:\s*(.*?)\n\s*blockers:\s*(.*?)\n\s*next_action:\s*(.*?)(?:\n|$)",
            output,
            re.DOTALL | re.IGNORECASE,
        )
        if seed_match:
            context_seed = (
                f"state: {seed_match.group(1).strip()}\n"
                f"pending: {seed_match.group(2).strip()}\n"
                f"blockers: {seed_match.group(3).strip()}\n"
                f"next_action: {seed_match.group(4).strip()}"
            )
            print(f"✅ Context seed extraido ({len(context_seed)} chars)")
            return output, code, context_seed

        return output, code, None

    # Fallback: modo manual
    print("📋 Nenhum cliente CLI configurado. Modo manual:")
    print("=" * 60)
    print(prompt[:3000])
    if len(prompt) > 3000:
        print(f"... (truncado — {len(prompt)} chars totais)")
    print("=" * 60)
    print("\nCole o prompt acima no seu terminal agentico e, ao finalizar,")
    print("certifique-se de que o output contenha um context_seed com:")
    print("  state: ...")
    print("  pending: ...")
    print("  blockers: ...")
    print("  next_action: ...")
    print(f"\n💡 Dica: defina LLC_AGENT_CLI=claude (ou opencode, codex, windsurf)")
    print("   para envio automatico via STDIN.")
    return "", 0, None
