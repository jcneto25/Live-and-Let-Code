# Thin Harness — Design Specification

**Versao:** 1.0.0
**Data:** 13 de Junho de 2026
**Status:** Design Aprovado
**Projeto:** Live and Let Code (LLC) — Thin Harness para orquestracao do pipeline
**Autor:** Equipe LLC

---

## 1. Visao Geral

### 1.1 Problema

O pipeline LLC atual exige que o usuario execute manualmente cada etapa: invocar a skill correta, inicializar a sessao ACE, copiar o context_seed, aguardar o agente, revisar o gate, finalizar a sessao, repetir. Sao ~88 acoes manuais para um pipeline completo de 11 steps. Isso introduz atrito, risco de erro e barreira de adocao.

### 1.2 Solucao

Um **Thin Harness** — camada de orquestracao de ~500 linhas em Python que conecta skills (Markdown), scripts ACE (Python) e o cliente de IA. O harness e "thin" por design: nao implementa tool-calling, nao define regras, nao ensina o modelo. Ele apenas conecta as pecas que ja existem.

### 1.3 Posicionamento Arquitetural

```
FAT SKILLS (Markdown)     ← docs/skills/ (14 arquivos)
     ↑
THIN HARNESS (Python)     ← .ace/scripts/llc.py + llc_harness.py (~500 linhas)
     ↑
FAT CODE (Python)         ← .ace/scripts/ (7 scripts ACE)
     ↑
CLIENTE DE IA             ← Claude Code, opencode, Codex, Cursor...
```

### 1.4 Decisoes de Design

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Posicao | A + B hibrido (CLI wrapper + pre/post hooks) | Dois modos de uso: `llc run` para step completo, `llc session start/end` para controle manual |
| Entry point | Ambos: `run` (step) + `pipeline` (completo) | Flexibilidade: steps individuais para dev, pipeline para onboarding |
| Invocacao do agente | Deteccao automatica com fallback manual | Tool-agnostic: funciona com qualquer cliente, inclusive sem CLI |
| Relacao com ACE | Harness invoca scripts ACE via subprocess | Nao substitui — orquestra. Scripts ACE permanecem independentes |
| Linguagem | Python 3.10+ (Click CLI) | Mesmo stack dos scripts ACE. Zero dependencias novas alem do Click |

---

## 2. Comandos CLI

```
llc run --step <N> [--prp <ID>] [--task "..."] [--no-worktree]
    Executa um step completo: init → skill → agente → gate → finalize

llc pipeline [--from <N>] [--to <N>]
    Executa steps em sequencia, parando em cada gate para aprovacao humana

llc session start --step <N> [--prp <ID>] [--task "..."]
    Inicializa ACE + worktree + carrega skill. Retorna prompt para colar no cliente

llc session end [--approve | --reject]
    Finaliza sessao: merge/discarta worktree, promove learning points, atualiza TASKS.md

llc gate --step <N>
    Exibe checklist do gate para revisao manual

llc status
    Progresso do pipeline: steps concluidos, sessao atual, worktrees ativos
```

---

## 3. Ciclo de Vida

### 3.1 `llc run` (step completo)

```
1. SESSION START
   ├─ initialize_session.py → session_id, context_seed
   └─ Se --prp ou step >= 11 → git worktree automatico

2. SKILL LOAD
   ├─ docs/skills/llc-step-{N}.md + AGENTS.md + context_seed
   └─ Monta prompt completo para o agente

3. AGENT INVOKE
   ├─ Detecta cliente CLI (claude, opencode, codex, cursor)
   ├─ Se detectado → invoca com --prompt
   └─ Se nao → exibe prompt para copiar/colar manual

4. GATE CHECK
   ├─ Exibe checklist do gate
   └─ Aguarda: [A]provar / [R]ejeitar

5. SESSION END
   ├─ <gate_result decision="approved|rejected">
   ├─ approved + worktree → merge + remove
   ├─ rejected + worktree → descarta
   ├─ Learning points promovidos → memory/
   └─ TASKS.md atualizado
```

### 3.2 `llc pipeline` (completo)

```
llc pipeline --from 0
├─ Step 0.5 → llc run --step 0.5 → Gate 1: [A/R]
├─ Step 1   → llc run --step 1   → Gate 2: [A/R]
├─ ...
└─ Step 11  → llc run --step 11  → Checkpoints QA
```

---

## 4. Invocacao do Agente

### 4.1 Deteccao automatica de cliente

Ordem de prioridade:
1. `claude` (Claude Code CLI)
2. `opencode` (opencode CLI)
3. `codex` (Codex CLI)
4. `cursor` (Cursor CLI)
5. Nenhum → modo manual (exibe prompt)

### 4.2 Montagem do prompt

```
┌─ AGENTS.md (convencoes, zonas, TDD, protocolo) ─┐
├─ llc-step-{N}.md (fat skill — processo do step) ─┤
├─ context_seed (estado da sessao anterior) ───────┤
└─ Instrucao de finalizacao ───────────────────────┘
```

### 4.3 Modo manual (fallback)

Exibe o prompt completo + instrucoes para copiar/colar. Apos conclusao, usuario executa `llc session end`.

---

## 5. Mapa de Arquivos

### 5.1 Novos

| Arquivo | Linhas | Responsabilidade |
|---------|:------:|-----------------|
| `.ace/scripts/llc.py` | ~300 | CLI principal: comandos Click |
| `.ace/scripts/llc_harness.py` | ~200 | Modulo interno: session, skill, agent, gate, finalize |

### 5.2 Modificados

| Arquivo | Mudanca |
|---------|---------|
| `LLC_GUIDE.md` | Substituir "Execute a skill..." por `llc run --step N` |
| `LLC_GUIDE.en.md` | Mirror EN |
| `llc-pipeline-design.md` | Adicionar secao do harness no diagrama de camadas |
| `FAQ.md` | "O que e o Thin Harness?" + tabela de beneficios |
| `FAQ.en.md` | Mirror EN |

---

## 6. Beneficios para o Usuario

| Dimensao | Sem harness | Com harness |
|----------|:-----------:|:-----------:|
| Acoes manuais por pipeline | ~88 | ~11 (so gates) |
| Risco de pular um step | Alto (manual) | Zero (orquestrado) |
| Risco de esquecer context_seed | Alto | Zero (automatico) |
| Consistencia entre sessoes | Manual (copiar/colar JSON) | Automatica |
| Curva de aprendizado | Precisa ler 3 docs | 1 comando |
| Worktree para PRPs paralelos | Precisa lembrar `--worktree` | Automatico (step >= 11) |
| Merge/descarte de worktrees | Manual | Automatico (por gate) |
| Learning points promovidos | Manual (script separado) | Automatico (finalize) |
| Onboarding de novo dev | ~30 min lendo guias | `llc pipeline --from 0` |

---

## 7. Relacao com Scripts ACE Existentes

O harness **nao substitui** os scripts ACE. Ele os **invoca** via subprocess:

```python
def session_start(step, prp, task):
    result = subprocess.run([
        "python", ".ace/scripts/initialize_session.py",
        "--step", str(step), "--prp", prp, "--task", task, "--json"
    ], capture_output=True)
    return json.loads(result.stdout)
```

Scripts ACE permanecem independentes e invocaveis manualmente. O harness e uma camada de conveniencia.

---

## 8. Controle de Versao

| Versao | Data | Autor | Alteracoes |
|--------|------|-------|------------|
| 1.0.0 | 13/06/2026 | Equipe LLC | Versao inicial do design do Thin Harness |
