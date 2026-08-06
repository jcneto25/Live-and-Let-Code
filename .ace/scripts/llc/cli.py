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

try:
    import click
except ImportError:
    print("❌ Click nao instalado. Execute: pip install click")
    sys.exit(1)

from llc_harness import (
    agent_invoke,
    gate_check,
    pipeline_run,
    session_end,
    session_start,
    skill_load,
    step_run,
)
from llc_steps import StepParamType
from llc_wave import format_wave_list, parse_execution_waves, parse_tasks, run_wave
from .gates_meta import (
    GATE_ALIASES,
    GATE_CHECKLIST,
    _get_gate_id,
    _show_gate_checklist,
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
@click.option(
    "--step",
    "-s",
    type=StepParamType(),
    required=True,
    help="Step LLC (id/alias/numero: 5, 0.5, security, 11.1)",
)
@click.option("--prp", "-p", default=None, help="ID do PRP (ex: PRP-001)")
@click.option("--task", "-t", default=None, help="Descricao da tarefa")
@click.option(
    "--wave",
    "-w",
    type=int,
    default=1,
    show_default=True,
    help="Numero da onda de execucao (EXECUTION_WAVES.md)",
)
@click.option(
    "--no-worktree", is_flag=True, help="Desativa isolamento via git worktree"
)
@click.option(
    "--auto-approve", is_flag=True, help="Aprova gates automaticamente (CI/CD)"
)
@click.option(
    "--delta",
    "-d",
    is_flag=True,
    help="Modo delta: ativa smart skip para este step",
)
@click.option(
    "--iteration",
    "-i",
    default=None,
    help="Identificador da iteracao (ex: v2)",
)
def run(step, prp, task, wave, no_worktree, auto_approve, delta, iteration):
    """Executa um step completo do pipeline LLC.

    Fluxo: init session -> load skill -> invoke agent -> gate check -> finalize session.
    """
    # Smart Skip no modo delta
    if delta:
        from llc_delta import (
            delta_report_exists,
            generate_skip_note,
            get_skip_reason,
            is_step_skipped,
            parse_delta_report,
        )
        if delta_report_exists():
            plan = parse_delta_report()
            if plan and is_step_skipped(step, plan):
                reason = get_skip_reason(step, "", plan) or "Step nao afetado"
                from llc_steps import normalize_step as _ns
                try:
                    name = _ns(step).name
                except Exception:
                    name = ""
                nf = generate_skip_note(step, name, reason, iteration=iteration)
                print(f"\n⏭️  Step {step} ({name}) — PULADO (Smart Skip)")
                print(f"   Motivo: {reason}")
                print(f"   Skip note: {nf}")
                return
        else:
            print("ℹ️  Modo delta ativado mas DELTA_REPORT.md nao encontrado.")
            print("   Execute 'llc pipeline --delta' primeiro.")

    print(f"\n🚀 LLC Run — Step {step} (wave {wave})")
    print(f"{'=' * 60}")

    sid = step_run(step, prp=prp, task=task, wave=wave, no_worktree=no_worktree)

    print()
    decision = gate_check(step, None, auto_approve=auto_approve)
    session_end(sid, decision, None, step=step)


@cli.command()
@click.option(
    "--from",
    "-f",
    "from_step",
    type=StepParamType(),
    default="0.5",
    help="Step inicial (id; default: 0.5)",
)
@click.option(
    "--to",
    "-t",
    "to_step",
    type=StepParamType(),
    default="11.1",
    help="Step final (id; default: 11.1)",
)
@click.option("--task", default=None, help="Descricao da tarefa (opcional)")
@click.option(
    "--quickstart",
    "-q",
    is_flag=True,
    help="Modo quickstart: 3 gates principais (1, 4, 11)",
)
@click.option(
    "--delta",
    "-d",
    is_flag=True,
    help="Modo delta: executa analise de impacto + smart skip",
)
@click.option(
    "--iteration",
    "-i",
    default=None,
    help="Identificador da iteracao (ex: v2, v3)",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    help="Aprova gates automaticamente (CI/CD)",
)
def pipeline(from_step, to_step, task, quickstart, delta, iteration, auto_approve):
    """Executa o pipeline LLC completo, parando em cada gate."""
    if quickstart:
        from_step = "0.5"
        to_step = "11"
        print("\n🚀 LLC Pipeline Quickstart")
        print(f"{'=' * 60}")
        print("Pipeline 0.5 → 11 (22 steps, todos os gates de especificação + segurança + arquitetura).")
        print("Modo completo (com OWASP/PRP-Verify/Arch-Fitness): llc pipeline --from 0 --to 11.1")
    elif delta:
        print(f"\n🚀 LLC Pipeline — Modo Delta (Iteracao: {iteration or 'N/A'})")
        print(f"{'=' * 60}")
    else:
        print(f"\n🚀 LLC Pipeline — Step {from_step} ate {to_step}")
        print(f"{'=' * 60}")

    success = pipeline_run(
        from_step=from_step, to_step=to_step, task=task,
        delta=delta, iteration=iteration, auto_approve=auto_approve,
    )
    if not success:
        sys.exit(1)


@cli.group()
def session():
    """Comandos de gerenciamento de sessao ACE."""
    pass


@session.command("start")
@click.option(
    "--step",
    "-s",
    type=StepParamType(),
    required=True,
    help="Step LLC (id/alias/numero)",
)
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

    context_seed = input(
        "Cole o context_seed gerado pelo agente (ou Enter para pular): "
    ).strip()
    session_end("manual", decision, context_seed or None)


@cli.command()
def status():
    """Exibe o progresso do pipeline e worktrees ativos."""
    import json
    import subprocess
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


@cli.group()
def gate():
    """Comandos de gate (validacao humana)."""
    pass


@click.command()
def gate_checklist(gate_id: str = None):
    """Exibe checklist de validacao de gates."""
    if gate_id:
        gate_id = _get_gate_id(gate_id)
        _show_gate_checklist(gate_id)
    else:
        click.echo("\nGates Disponiveis no Pipeline LLC")
        click.echo("=" * 50)
        for alias, gid in GATE_ALIASES.items():
            gate = GATE_CHECKLIST[gid]
            click.echo(f"\n  {gid} ({alias})")
            click.echo(f"    {gate['name']}")
        # Mostra gates sem alias
        for gid in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "11.5"]:
            if gid not in [v for v in GATE_ALIASES.values()]:
                click.echo(f"\n  Gate {gid}")


gate.add_command(gate_checklist)


@gate.command("run")
@click.option(
    "--gate",
    "-g",
    required=True,
    help="ID ou alias do gate (ex: security, null-safety, owasp, test-coverage, 10-coverage)",
)
@click.option(
    "--prp",
    "-p",
    default=None,
    help="ID do PRP (opcional, para gates específicos de PRP)",
)
@click.option(
    "--dry-run", "-n", is_flag=True, help="Apenas mostra o que seria verificado"
)
def gate_run(gate, prp, dry_run):
    """Validação manual de um gate (checklist + decisão humana).

    ⚠️ Este comando NÃO mede cobertura nem executa ferramentas: ele exibe o
    checklist do gate e aguarda a decisão A/R do operador. A cobertura real é
    verificada por `prp_verify` (step 10.8 / dente #9), que bloqueia o merge em
    caso de CRITICAL — use `prp_verify` para o limite efetivo de cobertura.
    """
    gate_id = _get_gate_id(gate)

    if dry_run:
        click.echo(f"\n[Dry-run] Gate {gate_id} seria executado")
        _show_gate_checklist(gate_id)
        return

    click.echo(f"\n🔍 Validando Gate {gate_id}")
    click.echo(f"{'=' * 50}")

    if gate_id == "10.8":
        click.echo(
            "ℹ️  Checklist manual — não mede cobertura. O limite real de cobertura "
            "(≥80% statements, 0 arquivos sem cobertura) é imposto por `prp_verify` "
            "(step 10.8 / dente #9), que bloqueia o merge em caso de CRITICAL."
        )

    # Executa o gate check
    decision = gate_check(gate_id, prp)

    if decision == "approved":
        click.echo(f"\n✅ Gate {gate_id}: APROVADO")
    else:
        click.echo(f"\n❌ Gate {gate_id}: REJEITADO")
        click.echo(f"   Motivo: {decision}")


@gate.command("list")
def gate_list():
    """Lista todos os gates disponíveis."""
    click.echo("\n📋 Gates Disponíveis no Pipeline LLC")
    click.echo(f"{'=' * 50}")

    for alias, gid in sorted(GATE_ALIASES.items()):
        gate = GATE_CHECKLIST[gid]
        click.echo(f"\n  🟡 {gid} (alias: {alias})")
        click.echo(f"    {gate['name']}")

    click.echo("\n" + "─" * 50)
    click.echo("\nGates de aprovação manual (steps 0.5 a 11.5):")
    click.echo("  Use 'llc run --step N' seguido de aprovação manual")


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
@click.option(
    "--aggregate",
    "-a",
    is_flag=True,
    help="Sessao unica para toda a wave (padrao: uma sessao por PRP)",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Apenas mostra o que seria executado, sem criar sessoes",
)
@click.option(
    "--no-worktree", is_flag=True, help="Desativa isolamento via git worktree"
)
@click.option(
    "--auto-approve", is_flag=True, help="Aprova gates automaticamente (CI/CD)"
)
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


# ── Delta commands ──


@cli.group()
def delta():
    """Comandos do fluxo delta (mudancas em sistema existente).

    Inicia a analise de impacto, executa smart skip e gerencia
    a iteracao entre versoes do sistema.
    """
    pass


@delta.command("start")
@click.option(
    "--iteration",
    "-i",
    required=True,
    help="Identificador da iteracao (ex: v2)",
)
@click.option(
    "--auto-approve", is_flag=True, help="Aprova gates automaticamente (CI/CD)"
)
def delta_start(iteration, auto_approve):
    """Inicia o fluxo delta: Step Δ.0 (Impact Analysis) + Step Δ.1 (Grill Me).

    1. Verifica se novos documentos existem em ingestion/
    2. Executa Step Δ.0 (gera DELTA_REPORT.md)
    3. Gate Δ.0 — validacao do relatorio de impacto
    4. Executa Step Δ.1 (Grill Me de Mudanca)
    5. Gate Δ.1 — validacao das respostas
    """
    print(f"\n{'='*60}")
    print(f"📊 INICIANDO FLUXO DELTA — Iteracao {iteration}")
    print(f"{'='*60}")

    from llc_delta import delta_report_exists

    from pathlib import Path as _P
    ingestion = _P("docs/business/ingestion/converted")
    if not ingestion.exists() or not list(ingestion.iterdir()):
        print("⚠️  Nenhum documento em docs/business/ingestion/converted/")
        print("   Coloque os novos documentos primeiro, ou execute:")
        print("   llc run --step 0.1  (conversao Docling)")
        return

    if delta_report_exists():
        print("ℹ️  DELTA_REPORT.md ja existe.")
        from click import confirm as _cf
        if not _cf("Deseja refazer a analise de impacto?"):
            print("   Pulando fase Δ. Use 'llc pipeline --delta' para continuar.")
            return

    from llc_harness import _run_delta_analysis

    success = _run_delta_analysis(
        auto_approve=auto_approve, iteration=iteration
    )
    if success:
        print(f"\n✅ Fluxo delta iniciado. Proximo passo:")
        print(f"   llc pipeline --delta --iteration {iteration}")
    else:
        print("\n⛔ Fluxo delta interrompido. Corrija e tente novamente.")


@delta.command("plan")
def delta_plan():
    """Exibe o plano de execucao delta atual (DELTA_REPORT.md)."""
    from llc_delta import parse_delta_report

    plan = parse_delta_report()
    if plan is None:
        print("❌ DELTA_REPORT.md nao encontrado.")
        print("   Execute: llc delta start --iteration v2")
        return

    print(f"\n📋 Plano Delta ({plan['change_type'].upper()})")
    print(f"{'='*60}")
    if plan["iteration"]:
        print(f"Iteracao: {plan['iteration']}")
    print(f"\nSteps a executar ({len(plan['execute_steps'])}):")
    for s in plan["execute_steps"]:
        print(f"  ✅ {s}")
    print(f"\nSteps a pular ({len(plan['skip_steps'])}):")
    for s in plan["skip_steps"]:
        print(f"  ⏭️  {s['step_id']} — {s['reason']}")
    if plan["affected_prps"]:
        print(f"\nPRPs afetados ({len(plan['affected_prps'])}):")
        for p in plan["affected_prps"]:
            print(f"  🔄 {p}")
    if plan["new_prps"]:
        print(f"\nNovos PRPs ({len(plan['new_prps'])}):")
        for p in plan["new_prps"]:
            print(f"  ✨ {p}")


@cli.group()
def eval():
    """Comandos de avaliação (Evals) — Pareto de custo×qualidade (PRP-EVALS-F5).

    Dashboard Pareto: ranking de steps por EfficiencyScore e ReworkWaste,
    gerado a partir dos baselines e resultados persistidos em .ace/evals/.
    """
    pass


@eval.command("ingest")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Apenas calcula os runs sem gravar baselines/estado",
)
@click.option(
    "--project-root",
    "project_root",
    default=None,
    help="Raiz do projeto (default: diretorio atual)",
)
def eval_ingest(dry_run, project_root):
    """Alimenta baselines a partir das sessões ACE (P1 pos-roadmap).

    Lê `<eval_metrics>` de `.ace/sessions/*.md` (appendado pelo
    finalize_session) e chama `BaselineManager.record_run()` — o elo que
    faltava para popular `.ace/evals/baselines/` (EVALS-F4 warm-up).
    Idempotente: re-execução não duplica runs.
    """
    from pathlib import Path as _Path

    from llc_evals.ingest import ingest_sessions

    root = _Path(project_root) if project_root else _Path.cwd()
    summary = ingest_sessions(
        sessions_dir=root / ".ace" / "sessions",
        baselines_dir=root / ".ace" / "evals" / "baselines",
        dry_run=dry_run,
    )
    mode = "dry-run" if dry_run else "ok"
    click.echo(
        f"\n📥 Eval Ingest [{mode}]: {summary['runs_recorded']} runs "
        f"({summary['blocks_found']} blocos, {summary['sessions_scanned']} sessões)"
    )
    click.echo(f"   Baselines: {root / '.ace' / 'evals' / 'baselines'}")
    if summary["errors"]:
        click.echo(f"   ⚠️  {len(summary['errors'])} erro(s) (ver detalhes no ingest)")
    else:
        click.echo("   ✅ Sem erros")


@eval.command("report")
@click.option(
    "--output",
    "-o",
    default=None,
    help="Diretório de saída (default: .ace/evals/results)",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Exibe o resumo em JSON (além do Markdown)",
)
def eval_report(output, as_json):
    """Gera o relatório Pareto Markdown (RF-EF5.3).

    Lê baselines (.ace/evals/baselines/) e resultados (.ace/evals/results/)
    e escreve report-{date}.md em .ace/evals/results/ (ou --output).
    """
    import json as _json
    from pathlib import Path as _Path

    from llc_evals.report import build_eval_summary, generate_report

    root = _Path.cwd()
    baselines_dir = root / ".ace" / "evals" / "baselines"
    results_dir = root / ".ace" / "evals" / "results"
    out_dir = _Path(output) if output else results_dir

    path = generate_report(
        baselines_dir=baselines_dir,
        results_dir=results_dir,
        output_dir=out_dir,
    )
    click.echo(f"\n📊 Eval Report gerado: {path}")

    summary = build_eval_summary(
        baselines_dir=baselines_dir, results_dir=results_dir,
    )
    click.echo(f"   Steps com baseline: {summary['steps_analyzed']}")
    if summary["worst_efficiency"]:
        w = summary["worst_efficiency"]
        click.echo(f"   🔻 Pior eficiência: step {w['step']} "
                   f"(eff {w['efficiency_score']:g}, fase {w['phase']})")
    if summary["highest_rework_waste"]:
        r = summary["highest_rework_waste"]
        click.echo(f"   🔻 Maior rework: step {r['step']} "
                   f"({r['rework_waste'] * 100:.0f}% tokens em retries)")

    if as_json:
        click.echo(_json.dumps(summary, indent=2, ensure_ascii=False))


@cli.command()
@click.option(
    "--from",
    "from_step",
    default=None,
    help="Step inicial do wizard (ex: 0.5)",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    help="Aprova gates automaticamente (sem HITL)",
)
@click.option(
    "--project-root",
    "project_root",
    default=None,
    help="Raiz do projeto (default: diretorio atual)",
)
@click.option(
    "--export-flow-metrics",
    is_flag=True,
    help="Exporta flow metrics (cycle/block time) para .ace/evals/results/ (RF-W1.2.3)",
)
def wizard(from_step, auto_approve, project_root, export_flow_metrics):
    """Inicia a TUI do Wizard (PRP-WIZARD-1A).

    Requer `textual` instalado; caso contrario, exibe a instrucao de instalacao
    e o prompt copy-paste (FallbackRunner). Com `--export-flow-metrics`, gera
    o YAML de métricas de fluxo (RF-W1.2.3) sem abrir a TUI.
    """
    if export_flow_metrics:
        from llc_wizard.flow_metrics import export_flow_metrics as _export

        root = Path(project_root) if project_root else Path.cwd()
        path = _export(root)
        click.echo(f"✅ Flow metrics exportadas: {path}")
        return

    try:
        import textual  # noqa: F401
    except ImportError:
        click.echo(
            "O Wizard requer a dependencia `textual`.\n"
            "Instale com: pip install textual\n"
            "Enquanto isso, rode os steps manualmente:"
        )
        from llc_wizard.runner import select_runner

        runner = select_runner(step_id=str(from_step or ""), task="")
        for event in _run_runner(runner):
            click.echo(event.text if hasattr(event, "text") else "")
        return

    from llc_wizard.app import WizardApp

    app = WizardApp(project_root=Path(project_root) if project_root else Path.cwd())
    click.echo("Iniciando Wizard (TUI)...")
    click.echo(f"  from: {from_step or 'inicio'} · auto-approve: {auto_approve}")


def _run_runner(runner):
    """Auxiliar: consome eventos de um runner (sincrono p/ CLI)."""
    import asyncio

    async def _consume():
        out = []
        async for ev in runner.run_step():
            out.append(ev)
        return out

    return asyncio.run(_consume())


if __name__ == "__main__":
    cli()