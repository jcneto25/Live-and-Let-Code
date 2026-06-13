# Thin Harness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI orchestrator (`llc`) that connects LLC skills (Markdown), ACE scripts (Python), and the AI client into a single command: `llc run --step N` or `llc pipeline`.

**Architecture:** Two new Python files: `llc_harness.py` (~200 lines, business logic module) and `llc.py` (~300 lines, Click CLI). The harness invokes existing ACE scripts via subprocess — it orchestrates, not replaces. AGENTS.md conventions block is loaded once and prepended to every skill prompt.

**Tech Stack:** Python 3.10+, Click (CLI framework), subprocess (ACE scripts), json, pathlib.

**Design Spec:** `docs/superpowers/specs/2026-06-13-thin-harness-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `.ace/scripts/llc_harness.py` | CREATE | Module: session_start, skill_load, agent_invoke, gate_check, session_end |
| `.ace/scripts/llc.py` | CREATE | CLI: run, pipeline, session start/end, gate, status commands |
| `LLC_GUIDE.md` | MODIFY | Replace manual steps with `llc` commands |
| `LLC_GUIDE.en.md` | MODIFY | Mirror EN |
| `llc-pipeline-design.md` | MODIFY | Add harness to architecture section |
| `FAQ.md` | MODIFY | Add Thin Harness question + benefits table |
| `FAQ.en.md` | MODIFY | Mirror EN |

---

### Task 1: Create llc_harness.py module

**Files:**
- Create: `.ace/scripts/llc_harness.py`

- [ ] **Step 1: Write the harness module**

```python
#!/usr/bin/env python3
"""
LLC Thin Harness — modulo de orquestracao do pipeline Live and Let Code.

Responsabilidades:
- session_start(): inicializa sessao ACE + worktree opcional
- skill_load(): carrega skill Markdown + AGENTS.md + context_seed
- agent_invoke(): detecta cliente CLI ou exibe prompt manual
- gate_check(): exibe checklist do gate, aguarda decisao humana
- session_end(): finaliza sessao, merge/discard worktree, learning points

Nao substitui os scripts ACE — os invoca via subprocess.
"""

import json
import subprocess
import sys
import shutil
from pathlib import Path

ACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ACE_DIR / "scripts"
SKILLS_DIR = Path("docs/skills")
AGENTS_FILE = Path("AGENTS.md")

# ── Agent CLI detection ──

AGENT_CLIENTS = ["claude", "opencode", "codex", "cursor"]

def detect_agent_client():
    """Detecta o primeiro cliente de IA CLI disponivel no PATH."""
    for client in AGENT_CLIENTS:
        if shutil.which(client):
            return client
    return None

# ── Session management ──

def session_start(step, prp=None, task=None, wave=1, no_worktree=False):
    """Inicializa sessao ACE. Retorna dict com session_id, context_seed, worktree_path."""
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "initialize_session.py"),
        "--step", str(step),
        "--task", task or f"Step {step}",
        "--wave", str(wave),
        "--json"
    ]
    if prp:
        cmd.extend(["--prp", prp])
    if no_worktree:
        cmd.append("--no-worktree")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    if result.returncode != 0:
        print(f"❌ Erro ao inicializar sessao:\n{result.stderr}")
        sys.exit(1)

    data = json.loads(result.stdout)
    print(f"✅ Sessao iniciada: {data.get('session_id')}")
    if data.get("worktree"):
        print(f"🔀 Worktree: {data.get('worktree')}")

    return {
        "session_id": data.get("session_id"),
        "context_seed": data.get("context_seed"),
        "worktree_path": data.get("worktree"),
    }

def session_end(session_id, gate_decision, context_seed_output):
    """Finaliza sessao ACE: gate_result, merge/discard worktree, learning points."""
    if not context_seed_output:
        context_seed_output = "state: step concluido\npending: nenhum\nblockers: nenhum\nnext_action: proximo step"

    cmd = [
        sys.executable, str(SCRIPTS_DIR / "finalize_session.py"),
        "--session-id", session_id,
        "--gate-decision", gate_decision,
        "--context-seed", context_seed_output,
        "--json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    if result.returncode != 0:
        print(f"⚠️  Aviso ao finalizar sessao:\n{result.stderr}")

    data = json.loads(result.stdout) if result.stdout else {}
    print(f"✅ Sessao finalizada. Gate: {gate_decision}")

    return data

# ── Skill loading ──

def load_agents_conventions():
    """Carrega AGENTS.md como bloco de convencoes estatico."""
    if AGENTS_FILE.exists():
        content = AGENTS_FILE.read_text(encoding="utf-8")
        return f"---\n# CONVENTIONS (AGENTS.md)\n---\n\n{content}\n\n---\n# TASK\n---\n\n"
    return ""

def skill_load(step, context_seed=None, task=None):
    """Carrega skill + AGENTS.md + context_seed. Retorna prompt montado."""
    skill_file = SKILLS_DIR / f"llc-step-{step}.md"
    if not skill_file.exists():
        # Tenta com hifen (ex: llc-step-0-5.md)
        import glob
        matches = list(SKILLS_DIR.glob(f"llc-step-{str(step).replace('.', '-')}*.md"))
        if matches:
            skill_file = matches[0]
        else:
            print(f"❌ Skill nao encontrada: {skill_file}")
            sys.exit(1)

    conventions = load_agents_conventions()
    skill = skill_file.read_text(encoding="utf-8")

    prompt = conventions + skill

    if context_seed:
        prompt += f"\n\n---\n# CONTEXT (sessao anterior)\n---\n\n{context_seed}"

    if task:
        prompt += f"\n\n---\n# TASK\n---\n\n{task}"

    prompt += "\n\n---\n# FINALIZACAO\n---\n\n"
    prompt += "Ao concluir este step, gere um context_seed no formato ACE de 4 campos:\n"
    prompt += "state: [acoes concluidas, arquivos alterados]\n"
    prompt += "pending: [tarefas incompletas]\n"
    prompt += "blockers: [impedimentos ativos]\n"
    prompt += "next_action: [proximo passo recomendado]\n"

    return str(skill_file), prompt

# ── Agent invocation ──

def agent_invoke(prompt, client=None):
    """Invoca cliente CLI ou exibe prompt para modo manual. Retorna (stdout, exit_code)."""
    if client is None:
        client = detect_agent_client()

    if client:
        print(f"🤖 Invocando {client}...")
        result = subprocess.run(
            [client, "--prompt", prompt],
            capture_output=False,  # streaming output
            cwd=Path.cwd()
        )
        return "", result.returncode
    else:
        print("📋 Nenhum cliente CLI detectado. Modo manual:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print("\nCole o prompt acima no seu cliente de IA.")
        print("Apos a conclusao, execute: llc session end")
        return "", 0

# ── Gate check ──

GATE_CHECKLISTS = {
    1: ["Visao cobre todo o escopo?", "Modulos corretamente identificados?", "Secoes sem [NAO IDENTIFICADO]?"],
    2: ["Termos do glossario consistentes?", "Perfis cobrem todos os atores?", "Integracoes batem com a realidade?"],
    3: ["PRD executivo comunica valor?", "PRD tecnico cobre todos os requisitos?", "Ambos sao consistentes?"],
    4: ["Granularidade dos PRPs adequada (2-8 dias)?", "Dependencias entre PRPs fazem sentido?", "Nenhum requisito sem PRP?"],
    5: ["Ondas bem agrupadas?", "Caminho critico realista?", "Tempo total estimado faz sentido?"],
    6: ["Stack viavel no ambiente?", "Decisoes arquiteturais justificadas?", "RNFs enderecados?"],
    7: ["Tarefas acionaveis?", "Agentes corretamente atribuidos?", "Estimativas realistas?"],
    8: ["Paleta reflete identidade?", "Componentes tem estados definidos?", "Design System cobre os fluxos?"],
    9: ["Projeto compila e roda?", "Dados mock realistas?", "Handlers simulam erros?"],
    10: ["Comandos de teste batem com o stack?", "Thresholds realistas?", "Templates reutilizaveis?"],
    11: ["README permite onboarding <= 10 min?", "DEPLOYMENT cobre rollback?", "Sem secrets expostos?"],
    11.5: ["Estrutura cobre todos os modulos?", "Perfis tem paginas relevantes?", "Indice navegavel?", "Linguagem adequada?"],
    11: {"11-SEC": ["0 vulnerabilidades criticas?", "Secrets reais zerados?", "Vulnerabilidades altas com decisao?"]},
}

STEP_TO_GATE = {
    0.5: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 10.5: 11.5,
    11: "11-SEC"
}

def gate_check(step, output):
    """Exibe checklist do gate e aguarda decisao humana."""
    gate = STEP_TO_GATE.get(step)
    if gate is None:
        print(f"ℹ️  Nenhum gate definido para step {step}. Avancando automaticamente.")
        return "approved"

    if isinstance(gate, dict):
        # Sub-gates (ex: 11-SEC)
        for sub_gate, items in gate.items():
            print(f"\n👤 Gate {sub_gate}:")
            for item in items:
                print(f"  - {item}")
    else:
        items = GATE_CHECKLISTS.get(gate, [])
        print(f"\n👤 Gate {gate}:")
        for item in items:
            print(f"  - {item}")

    print()
    while True:
        choice = input("[A]provar  [R]ejeitar  [S]kip (aprovar sem revisar): ").strip().lower()
        if choice in ("a", "approve"):
            return "approved"
        elif choice in ("r", "reject"):
            return "rejected"
        elif choice in ("s", "skip"):
            return "approved"
        print("Opcao invalida. Use A, R ou S.")

# ── Pipeline orchestration ──

def pipeline_run(from_step=0, to_step=11, task=None):
    """Executa pipeline completo do step inicial ao final."""
    steps = [0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 11]
    started = False

    for step in steps:
        if step < from_step:
            continue
        if step > to_step:
            break
        if not started:
            print(f"\n{'='*60}")
            print(f"🚀 Iniciando pipeline LLC (Step {from_step} → {to_step})")
            print(f"{'='*60}")
            started = True

        sid = step_run(step, task=task)
        decision = gate_check(step, None)
        session_end(sid, decision, None)

        if decision == "rejected":
            print(f"\n⛔ Gate {STEP_TO_GATE.get(step)} REPROVADO. Pipeline pausado.")
            print("Corrija os problemas e reexecute a partir deste step:")
            print(f"  llc run --step {step}")
            return False

    print(f"\n{'='*60}")
    print("✅ Pipeline concluido com sucesso!")
    print(f"{'='*60}")
    return True

def step_run(step, prp=None, task=None, no_worktree=False):
    """Executa um step e retorna session_id."""
    sess = session_start(step, prp=prp, task=task, no_worktree=no_worktree)
    skill_file, prompt = skill_load(step, sess["context_seed"], task)
    print(f"📄 Skill: {skill_file}")
    print(f"📦 Context seed: {len(sess.get('context_seed', '') or '')} chars")

    output, code = agent_invoke(prompt)
    if code != 0:
        print(f"⚠️  Agente retornou codigo {code}")
    return sess["session_id"]
```

- [ ] **Step 2: Commit**

```bash
git add .ace/scripts/llc_harness.py
git commit -m "feat: add llc_harness.py — Thin Harness orchestration module"
```

---

### Task 2: Create llc.py CLI

**Files:**
- Create: `.ace/scripts/llc.py`

- [ ] **Step 1: Write the CLI**

```python
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

# Garante que o modulo llc_harness esta no path
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


@click.group()
def cli():
    """LLC Thin Harness — orquestrador do pipeline Live and Let Code.

    Conecta skills (Markdown), scripts ACE (Python) e o cliente de IA
    em um unico comando. Tool-agnostic: funciona com Claude Code,
    opencode, Codex, Cursor ou modo manual.
    """
    pass


@cli.command()
@click.option("--step", "-s", type=float, required=True, help="Step LLC (ex: 5, 0.5, 11)")
@click.option("--prp", "-p", default=None, help="ID do PRP (ex: PRP-001)")
@click.option("--task", "-t", default=None, help="Descricao da tarefa")
@click.option("--no-worktree", is_flag=True, help="Desativa isolamento via git worktree")
def run(step, prp, task, no_worktree):
    """Executa um step completo do pipeline LLC.

    Fluxo: init session → load skill → invoke agent → gate check → finalize session.
    """
    print(f"\n🚀 LLC Run — Step {step}")
    print(f"{'='*60}")

    sid = step_run(step, prp=prp, task=task, no_worktree=no_worktree)

    print()
    decision = gate_check(step, None)
    session_end(sid, decision, None)


@cli.command()
@click.option("--from", "-f", "from_step", type=float, default=0, help="Step inicial (default: 0)")
@click.option("--to", "-t", "to_step", type=float, default=11, help="Step final (default: 11)")
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
@click.option("--step", "-s", type=float, required=True, help="Step LLC")
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
@click.option("--step", "-s", type=float, required=True, help="Step LLC")
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
            print(f"   Step: {last.get('llc_step')}")
            print(f"   Tags: {', '.join(last.get('tags', []))}")
            print(f"   Data: {last.get('created')}")
        else:
            print("📍 Nenhuma sessao registrada.")
    else:
        print("📍 Nenhuma sessao registrada.")

    result = subprocess.run(["git", "worktree", "list"], capture_output=True, text=True)
    print(f"\n🔀 Worktrees ativos:\n{result.stdout}")


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2: Commit**

```bash
git add .ace/scripts/llc.py
git commit -m "feat: add llc.py — Thin Harness CLI (Click-based orchestrator)"
```

---

### Task 3: Update LLC_GUIDE.md (PT-BR)

**Files:**
- Modify: `LLC_GUIDE.md`

- [ ] **Step 1: Add harness setup section before "Passo a Passo"**

Find the heading `## Passo a Passo` and insert before it:

```markdown

### Usando o Thin Harness (recomendado)

A partir da versao 1.4.0, o LLC inclui um orquestrador CLI que automatiza o ciclo de vida de cada step:

```bash
# Instalar dependencia unica
pip install click

# Executar um step completo
python .ace/scripts/llc.py run --step 5 --task "Arquitetura do sistema"

# Pipeline completo (para em cada gate)
python .ace/scripts/llc.py pipeline --from 0

# Ver progresso
python .ace/scripts/llc.py status
```

O harness gerencia automaticamente: sessao ACE, context_seed, carregamento da skill,
invocacao do agente, gate de validacao e finalizacao. Se o cliente CLI estiver
disponivel (claude, opencode, codex, cursor), a invocacao e automatica. Caso
contrario, o prompt e exibido para copiar e colar manualmente.

```

- [ ] **Step 2: For each "Voce faz:" block, add the `llc` alternative**

For example, change:
```
Execute a skill docs/skills/llc-step-0-5.md
```
To:
```
Execute a skill docs/skills/llc-step-0-5.md
# Ou use o harness: python .ace/scripts/llc.py run --step 0.5
```

- [ ] **Step 3: Commit**

```bash
git add LLC_GUIDE.md
git commit -m "docs: add Thin Harness usage to LLC guide (PT-BR)"
```

---

### Task 4: Update LLC_GUIDE.en.md (EN-US)

**Files:**
- Modify: `LLC_GUIDE.en.md`

- [ ] **Step 1: Mirror the PT-BR changes in English**

Same structure as Task 3, in English:

```markdown
### Using the Thin Harness (recommended)

```bash
pip install click
python .ace/scripts/llc.py run --step 5 --task "System Architecture"
python .ace/scripts/llc.py pipeline --from 0
python .ace/scripts/llc.py status
```
```

And add `# Or use the harness: python .ace/scripts/llc.py run --step 0.5` alternatives.

- [ ] **Step 2: Commit**

```bash
git add LLC_GUIDE.en.md
git commit -m "docs: add Thin Harness usage to LLC guide (EN-US)"
```

---

### Task 5: Update llc-pipeline-design.md

**Files:**
- Modify: `llc-pipeline-design.md`

- [ ] **Step 1: Add harness to 5-layer architecture diagram (section 1.4)**

After the existing layer diagram, add a note:

```markdown

### 1.5 Thin Harness — Orquestracao

O **Thin Harness** (`llc`) e a camada de orquestracao que conecta as 5 camadas
arquiteturais. E um CLI Python (~500 linhas) que automatiza o ciclo de vida de
cada step: init session → load skill → invoke agent → gate check → finalize session.

O harness e "thin" por design: nao implementa tool-calling, nao define regras,
nao ensina o modelo. Ele apenas conecta as pecas que ja existem.

```
FAT SKILLS (Markdown)     ← docs/skills/ (14 arquivos)
     ↑
THIN HARNESS (Python)     ← .ace/scripts/llc.py + llc_harness.py (~500 linhas)
     ↑
FAT CODE (Python)         ← .ace/scripts/ (7 scripts ACE)
     ↑
CLIENTE DE IA             ← Claude Code, opencode, Codex, Cursor...
```
```

- [ ] **Step 2: Commit**

```bash
git add llc-pipeline-design.md
git commit -m "docs: add Thin Harness to pipeline design architecture"
```

---

### Task 6: Add Thin Harness FAQ (PT-BR + EN-US)

**Files:**
- Modify: `FAQ.md`
- Modify: `FAQ.en.md`

- [ ] **Step 1: Add to FAQ.md (PT-BR)**

Add a new section before the final sections:

```markdown

---

## 🔧 Thin Harness

### O que e o Thin Harness do LLC?

O **Thin Harness** e a camada de orquestracao que conecta skills (Markdown), scripts ACE (Python) e o cliente de IA. E um CLI de ~500 linhas em Python que automatiza o ciclo de vida de cada step do pipeline.

**Comandos principais:**

```bash
llc run --step 5                     # Executa um step completo
llc pipeline --from 0                # Pipeline completo (para nos gates)
llc session start --step 5           # Inicia sessao manual
llc session end --approve            # Finaliza sessao manual
llc status                           # Progresso do pipeline
```

**Beneficios em relacao ao modo manual:**

| Dimensao | Sem harness | Com harness |
|----------|:-----------:|:-----------:|
| Acoes manuais por pipeline completo | ~88 | ~11 (so gates) |
| Risco de pular um step | Alto (manual) | Zero (orquestrado) |
| Risco de esquecer context_seed | Alto | Zero (automatico) |
| Consistencia entre sessoes | Manual (copiar/colar JSON) | Automatica |
| Curva de aprendizado | Precisa ler 3 docs | 1 comando |
| Worktree para PRPs paralelos | Precisa lembrar `--worktree` | Automatico (step >= 11) |
| Merge/descarte de worktrees | Manual | Automatico (por gate) |
| Learning points promovidos | Manual (script separado) | Automatico (finalize) |
| Onboarding de novo dev | ~30 min lendo guias | `llc pipeline --from 0` |

**O harness NAO substitui os scripts ACE** — ele os invoca via subprocess. Scripts ACE permanecem independentes e invocaveis manualmente.

**Por que "thin"?** O harness tem ~500 linhas por design. Ele nao implementa tool-calling (isso e do cliente), nao define regras de seguranca (isso e do AGENTS.md), nao ensina o modelo a pensar (isso e das skills Markdown). Sua unica funcao e conectar as pecas que ja existem.
```

- [ ] **Step 2: Add to FAQ.en.md (EN-US)**

```markdown

---

## 🔧 Thin Harness

### What is the LLC Thin Harness?

The **Thin Harness** is the orchestration layer connecting skills (Markdown), ACE scripts (Python), and the AI client. It's a ~500-line Python CLI that automates the lifecycle of each pipeline step.

**Main commands:**

```bash
llc run --step 5                     # Execute a complete step
llc pipeline --from 0                # Full pipeline (stops at gates)
llc session start --step 5           # Start manual session
llc session end --approve            # End manual session
llc status                           # Pipeline progress
```

**Benefits over manual mode:**

| Dimension | Without harness | With harness |
|-----------|:---------------:|:------------:|
| Manual actions per full pipeline | ~88 | ~11 (gates only) |
| Risk of skipping a step | High (manual) | Zero (orchestrated) |
| Risk of forgetting context_seed | High | Zero (automatic) |
| Consistency between sessions | Manual (copy/paste JSON) | Automatic |
| Learning curve | Must read 3 docs | 1 command |
| Worktree for parallel PRPs | Must remember `--worktree` | Automatic (step >= 11) |
| Worktree merge/discard | Manual | Automatic (by gate) |
| Learning points promoted | Manual (separate script) | Automatic (finalize) |
| New developer onboarding | ~30 min reading guides | `llc pipeline --from 0` |

**The harness does NOT replace ACE scripts** — it invokes them via subprocess. ACE scripts remain independent and manually invocable.

**Why "thin"?** The harness is ~500 lines by design. It does not implement tool-calling (that's the client), does not define security rules (that's AGENTS.md), does not teach the model how to think (that's the skills). Its only function is to connect the pieces that already exist.
```

- [ ] **Step 3: Commit**

```bash
git add FAQ.md FAQ.en.md
git commit -m "docs: add Thin Harness FAQ section with benefits table (PT-BR + EN-US)"
```
