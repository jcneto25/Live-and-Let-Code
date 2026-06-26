#!/usr/bin/env python3
"""
LLC Thin Harness — CLI orquestrador do pipeline Live and Let Code.

Uso:
  llc run --step 5 --task "Arquitetura do sistema"
  llc pipeline --from 0 --to 10
  llc session start --step 5
  llc session end --approve
  llc gate --step 5
  llc status

Requer: Python 3.10+, Click (pip install click)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import click
except ImportError:
    print("❌ Click nao instalado. Execute: pip install click")
    sys.exit(1)

from llc_harness import (
    session_start, session_end, skill_load, agent_invoke,
    gate_check, pipeline_run, step_run
)
from llc_steps import StepParamType
from llc_wave import (
    parse_execution_waves, parse_tasks, format_wave_list, run_wave
)


@click.group()
def cli():
    """LLC Thin Harness — orquestrador do pipeline Live and Let Code.

    Conecta skills (Markdown), scripts ACE (Python) e o cliente de IA
    em um unico comando. Tool-agnostic: funciona com Claude Code,
    opencode, Codex, Cursor ou modo manual.
    """
    pass


@cli.command()
@click.option("--step", "-s", type=StepParamType(), required=True, help="Step LLC (id/alias/numero: 5, 0.5, security, 11.1)")
@click.option("--prp", "-p", default=None, help="ID do PRP (ex: PRP-001)")
@click.option("--task", "-t", default=None, help="Descricao da tarefa")
@click.option("--wave", "-w", type=int, default=1, show_default=True, help="Numero da onda de execucao (EXECUTION_WAVES.md)")
@click.option("--no-worktree", is_flag=True, help="Desativa isolamento via git worktree")
@click.option("--auto-approve", is_flag=True, help="Aprova gates automaticamente (CI/CD)")
def run(step, prp, task, wave, no_worktree, auto_approve):
    """Executa um step completo do pipeline LLC.

    Fluxo: init session -> load skill -> invoke agent -> gate check -> finalize session.
    """
    print(f"\n🚀 LLC Run — Step {step} (wave {wave})")
    print(f"{'='*60}")

    sid = step_run(step, prp=prp, task=task, wave=wave, no_worktree=no_worktree)

    print()
    decision = gate_check(step, None, auto_approve=auto_approve)
    session_end(sid, decision, None, step=step)


@cli.command()
@click.option("--from", "-f", "from_step", type=StepParamType(), default="0.5", help="Step inicial (id; default: 0.5)")
@click.option("--to", "-t", "to_step", type=StepParamType(), default="11.1", help="Step final (id; default: 11.1)")
@click.option("--task", default=None, help="Descricao da tarefa (opcional)")
def pipeline(from_step, to_step, task):
    """Executa o pipeline LLC completo, parando em cada gate."""
    success = pipeline_run(from_step=from_step, to_step=to_step, task=task)
    if not success:
        sys.exit(1)


@cli.group()
def session():
    """Comandos de gerenciamento de sessao ACE."""
    pass


@session.command("start")
@click.option("--step", "-s", type=StepParamType(), required=True, help="Step LLC (id/alias/numero)")
@click.option("--prp", "-p", default=None, help="ID do PRP")
@click.option("--task", "-t", default=None, help="Descricao da tarefa")
def session_start_cmd(step, prp, task):
    """Inicializa sessao ACE + carrega skill. Retorna prompt para modo manual."""
    sess = session_start(step, prp=prp, task=task)
    skill_file, prompt = skill_load(step, sess["context_seed"], task)
    print(f"\n📄 Skill: {skill_file}")
    print(f"📦 Context seed: {len(sess.get('context_seed', '') or '')} chars")
    print(f"\n🔀 Worktree: {sess.get('worktree_path') or 'N/A'}")
    print(f"\n📋 Sessao pronta. Use o cliente de IA para executar o step.")
    print(f"   Apos conclusao, execute: llc session end --approve")


@session.command("end")
@click.option("--approve", "decision", flag_value="approved", help="Aprovar gate")
@click.option("--reject", "decision", flag_value="rejected", help="Rejeitar gate")
def session_end_cmd(decision):
    """Finaliza sessao ACE. Use --approve ou --reject."""
    if not decision:
        decision = input("Decisao do gate? [A]provar [R]ejeitar: ").strip().lower()
        decision = "approved" if decision in ("a", "approve") else "rejected"

    context_seed = input("Cole o context_seed gerado pelo agente (ou Enter para pular): ").strip()
    session_end("manual", decision, context_seed or None)


@cli.command()
@click.option("--step", "-s", type=StepParamType(), required=True, help="Step LLC (id/alias/numero)")
def gate(step):
    """Exibe o checklist do gate para revisao manual."""
    decision = gate_check(step, None)
    print(f"\nGate decision: {decision}")


@cli.command()
def status():
    """Exibe o progresso do pipeline e worktrees ativos."""
    import subprocess
    import json
    from pathlib import Path

    index_file = Path(".ace/index.json")
    if index_file.exists():
        data = json.loads(index_file.read_text())
        sessions = data.get("sessions", [])
        if sessions:
            last = sessions[-1]
            print(f"📍 Ultima sessao: {last.get('session_id')}")
            print(f"   Step: {last.get('llc_step_id') or last.get('llc_step')}")
            print(f"   Tags: {', '.join(last.get('tags', []))}")
            print(f"   Data: {last.get('timestamp')}")
        else:
            print("📍 Nenhuma sessao registrada.")
    else:
        print("📍 Nenhuma sessao registrada.")

    result = subprocess.run(["git", "worktree", "list"], capture_output=True, text=True)
    print(f"\n🔀 Worktrees ativos:\n{result.stdout}")


# ── Wave execution ──


@cli.group()
def wave():
    """Comandos de execucao por ondas (EXECUTION_WAVES.md).

    Le a estrutura de ondas e PRPs do arquivo de planejamento e
    itera automaticamente, abrindo sessoes ACE por PRP ou agregadas.
    """
    pass


@wave.command("list")
def wave_list():
    """Lista todas as ondas e seus PRPs."""
    waves = parse_execution_waves()
    prps = parse_tasks()
    output = format_wave_list(waves, prps)
    click.echo(output)


@wave.command("run")
@click.option("--wave", "-w", type=int, required=True, help="Numero da onda (ex: 1)")
@click.option("--aggregate", "-a", is_flag=True, help="Sessao unica para toda a wave (padrao: uma sessao por PRP)")
@click.option("--dry-run", "-n", is_flag=True, help="Apenas mostra o que seria executado, sem criar sessoes")
@click.option("--no-worktree", is_flag=True, help="Desativa isolamento via git worktree")
@click.option("--auto-approve", is_flag=True, help="Aprova gates automaticamente (CI/CD)")
def wave_run(wave, aggregate, dry_run, no_worktree, auto_approve):
    """Executa uma onda: itera PRPs e abre sessoes ACE."""
    success = run_wave(
        wave_num=wave,
        aggregate=aggregate,
        dry_run=dry_run,
        no_worktree=no_worktree,
        auto_approve=auto_approve,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    cli()
