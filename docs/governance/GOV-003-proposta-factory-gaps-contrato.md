# GOV-003: Proposta factory-evolution com conflitos de contrato e gaps semânticos vs workflow atual

**Status**: open
**Data de abertura**: 2026-08-05
**Data de instalação**: (pendente)
**Data de fechamento**: (pendente)
**Step de origem**: 11.4 (auditoria pré-execução da proposta factory-evolution, solicitada pelo operador)
**PRP relacionado**: PRP-MAP (Trilhas 0–3) · PRP-ACE-TAGS (a criar — ver Decisão, R1)

## Sintoma

Auditoria cruzada da proposta de evolução (`factory-evolution.md` v0.2.0, ADRs
0002/0004/0005/0006, 20 PRPs em `docs/prps/`, `PRP-MAP.md`) contra o estado real do
repositório encontrou **3 conflitos bloqueantes (🔴), 8 gaps semânticos (🟡) e 5 drifts
documentais (🟢)** entre os artefatos aceitos e os mecanismos determinísticos atuais.

Nenhum conflito é filosófico — os princípios (human-in-control, determinismo,
tool-agnostic, ACE append-only) são preservados pela proposta. Todos os conflitos são
de **schema e contrato de implementação**, detectados **antes** da execução da Trilha 0.

## Contexto

Em 2026-08-05, antes de iniciar a execução do PRP-MAP, o operador solicitou verificação
de consistência da proposta. A auditoria leu todos os artefatos da proposta e verificou
fatos contra o código: `validate-tags.py`, `llc_steps/models.py` + `registry.py`,
`.ace/index.json`, `.ace/config/gates.json`, `.ace/scripts/llc_harness/session.py`.

## Classe de Falha

Falha Estrutural (documental/contratual) — ADRs `accepted` contêm premissas factualmente
incorretas sobre o código e formatos de serialização incompatíveis com mecanismos
determinísticos vigentes. A proposta foi gerada em múltiplos documentos paralelos,
derivados uns dos outros, sem verificação cruzada contra o repositório.

## Impacto

Alto — se a execução fosse iniciada sem correção:

1. **WIZARD-1B e EVALS-F1 quebrariam no pre-commit**: as tags `<user_response>`,
   `<eval_metrics>` e o formato `<gate_result approved= waiver=>` do ADR-0002 §7.2
   falham no `validate-tags.py` (que roda via `validate-tags.py --coverage` no hook).
2. **PRP-GRAPH-1A construiria sobre fonte inexistente**: RF-G1A.3 exige `depends_on`
   do registry de steps, campo que não existe em `StepSpec`.
3. **Retrabalho garantido no Kanban**: ADR-0002 (adapter) e ADR-0004 §8.3 (refactor
   direto) prescrevem direções opostas para a mesma integração — o primeiro a ser
   implementado seria desfeito pelo segundo.

## Evidência

Verificado em 2026-08-05 (sessão 2026-08-05-001):

| # | Afirmação da proposta | Fato no repositório |
|---|---|---|
| C1 | ADR-0002 §7.2: `<gate_result approved="true" waiver="true">`; tags `<user_response>`, `<eval_metrics>` | `validate-tags.py`: `REQUIRED_ATTRS["gate_result"] = ["step","decision"]`; `BALANCED_TAGS` não inclui `user_response`, `eval_metrics` **nem `task_completed`** (gap pré-existente do AGENTS.md) |
| C2 | ADR-0004 §1.1/D2: "`step.depends_on` no registry" | `llc_steps/models.py`: `StepSpec` = `id, number, name, skill_file, gate, in_pipeline, auto_worktree, aliases` — **sem `depends_on`** |
| C3 | ADR-0002 P7/D6 + PRP-WIZARD-1A §7.5: migração via adapter "sem tocar kanban.py" | ADR-0004 §8.3 + PRP-GRAPH-1C RF-G1C.3: "`KanbanBoardBuilder` **refatorado** para receber `GraphEngine`" |
| G1 | `StepStatus` do Wizard com 7 estados | `index.json` só registra `in_progress`/`completed`; `gate_pending`/`failed`/`skipped`/`excluded` sem derivação especificada |
| G2 | Cards N2 (PRPs em worktrees) no Kanban | Sessões no `index.json` não têm campo `prp` (keys: `session_id, file, status, llc_step, llc_step_id, tags, timestamp`); fonte N2 inespecificada |
| G3 | `GateItem.required: bool` (PRP-WIZARD-1A §7.2) | `gates.json` checklist é lista de strings; RF-W1A.5 usa chave `"gate-1"` (reais: `"1"`); alterar `gates.json` dispara Autoridade de Conversão (GOV-001/ADR-0001) |
| G4 | PRP-MAP: EVALS-F1 depende de WIZARD-1A | ADR-0005 é transversal; F1 instrumenta `finalize_session.py` — não precisa do Wizard; serializa ~2 semanas sem necessidade |
| G5 | PRP-MAP caminho crítico: GOV→1A→1.1→GRAPH-1C | Omite GRAPH-1A (1 sem) e GRAPH-1B (1,5 sem), pré-requisitos de 1C; real: GOV→1A→GRAPH-1A→1B→1C (6,5 sem) |
| G6 | GOV-002 item 2 (llm_fallback fail-fast) → PRP-GOV-004 | PRP-GOV-004 não consta no PRP-MAP; `FallbackRunner` do Wizard herda o caminho do bug |
| G7 | ADR-0002 P2: "sessões escritas apenas pelos scripts sancionados" | O próprio ADR-0002 §2.4 cria `UserDecisionWriter` (3º escritor) — auto-contradição com AGENTS.md ("os ÚNICOS": initialize/finalize) |
| G8 | `impact_of()` formal no GraphEngine | Nenhum PRP conecta `impact-analyzer.py`/Smart Skip existentes ao engine — duas lógicas divergentes coexistiriam |
| D1–D5 | Drifts: ADRs em `docs/architecture/` flat (deveriam estar em `adr/`); numeração ADR-001 vs ADR-0002; `docs/roadmap/` inexistente (factory-evolution está em `docs/architecture/`); alignment v1.8.0 (atual: v1.9.0); gate `dependency-admission` não registrado em `gates.json` | verificado em `ls` e headers dos documentos |

## Causa Estrutural

A proposta foi elaborada como conjunto de documentos inter-referenciados **sem um passo
de fact-check contra o repositório**: cada ADR citava o outro e assumia fatos do código
(campos do `StepSpec`, schema do `index.json`, taxonomia de tags do validador) sem
verificá-los. O pipeline LLC tem gates para artefatos de projeto (Visão → Specs → PRDs →
PRPs), mas **não tem gate de verificação factual para ADRs que descrevem o próprio
tooling** — a mesma classe de "advisory onde deveria ser determinístico" que motivou
GOV-001, aqui na forma "documento aceito onde deveria haver verificação".

## Decisão

**Resposta de Controle (plano de harmonização R1–R12)** — executar antes e durante a
Trilha 0. Nenhuma emenda muda o mérito da proposta; todas alinham contratos.

### Bloco 1 — Bloqueantes (pré-requisito para qualquer PRP do mapa)

| # | Ação | Documentos afetados |
|---|---|---|
| **R1** | Criar **PRP-ACE-TAGS** (Trilha 0, ~2d, TDD): atualizar `BALANCED_TAGS`/`REQUIRED_ATTRS`/`VALID_VALUES` do `validate-tags.py` com `user_response`, `eval_metrics`, `task_completed`, `waiver_note`; alinhar formato `<gate_result>` do ADR-0002 ao schema atual (`step`/`decision` + `waiver` como atributo opcional); emendar pipeline-design §8.4 (taxonomia) | `validate-tags.py`, `llc-pipeline-design.md`, ADR-0002 §7.2, PRP-MAP Trilha 0 |
| **R2** | Emendar fonte da estrutura do grafo: arestas N1 derivadas da **ordem sequencial do REGISTRY (`StepSpec.number`) + `gates.json`** — zero mudança no harness (preserva ADR-0004 §2.9 "intocados") | ADR-0004 §1.1/D2, PRP-GRAPH-1A RF-G1A.3 |
| **R3** | Fixar estratégia **adapter**: `KanbanBoardBuilder` continua recebendo `PipelineDataSource` Protocol; migração = implementação `GraphEngine`-backed do Protocol injetada, sem tocar `kanban.py`/`app.py` | ADR-0004 §8.3, PRP-GRAPH-1C RF-G1C.3 (reescrito; RF-G1C.4 paridade mantido) |

### Bloco 2 — Altos (resolver durante a Trilha 0, antes dos PRPs afetados)

| # | Ação | Documentos afetados |
|---|---|---|
| **R4** | Adicionar tabela de derivação `StepStatus`↔fonte (`gate_pending`/`failed`/`skipped`/`excluded`) e regra `GateItem.required` (default `true` para todos os itens do checklist) | PRP-WIZARD-1A §2/§7 |
| **R5** | Definir fonte N2: gravar campo `prp` no `index.json` via `initialize_session.py` (já recebe `--prp`) — requer ADR curto de schema ACE; alternativa documentada: `git worktree list` | PRP-WIZARD-1.1, ADR novo, `initialize_session.py` |
| **R6** | Corrigir caminho crítico (via GRAPH-1A→1B) e marcar EVALS-F1/F2 como **paralelos** ao WIZARD-1A (dependência apenas de GOV-T3) | `PRP-MAP.md` |
| **R7** | Incluir fix do `llm_fallback` (GOV-002 Decisão item 2: falhar explicitamente pedindo `--step`/`--task` reais) como bloqueio de PRP-WIZARD-1A; referenciar PRP-GOV-004 no mapa | `PRP-MAP.md`, GOV-002, `.ace/scripts/llc/` |
| **R8** | Emendar AGENTS.md sancionando `UserDecisionWriter` (append-only) e o append de `<eval_metrics>` **dentro de** `finalize_session.py` (escritor único preservado) | `AGENTS.md`, ADR-0002 P2, PRP-EVALS-F1 |

### Bloco 3 — Drifts documentais (qualquer momento)

| # | Ação | Documentos afetados |
|---|---|---|
| **R9** | Mover ADRs 0002/0004/0005/0006 para `docs/architecture/adr/`; padronizar numeração; corrigir path do factory-evolution (`docs/roadmap/` inexistente) e alignment para v1.9.0 | arquivos afetados, `llc-pipeline-design.md` §2.1/§7.2 |
| **R10** | Registrar `dependency-admission` em `gates.json` **ou** declará-lo checklist de PR (não gate de pipeline) — se em `gates.json`, commit carrega este GOV (Autoridade de Conversão) | ADR-0006 §5.2, `gates.json` |
| **R11** | Registrar decisão: `impact-analyzer.py`/Smart Skip migram para `GraphEngine.impact_of()` no PRP-GRAPH-1B (ou coexistência declarada com justificativa) | PRP-GRAPH-1B, `impact-analyzer.py` |
| **R12** | Alinhar narrativa de investimento: ~12 semanas = MVP núcleo (GOV+1A+EVALS F1/F2+GRAPH 1A–1C); ~24 semanas = trilha completa | `factory-evolution.md` §4, `PRP-MAP.md` |

## Mecanismo Instalado

- Este GOV (registro da auditoria + plano R1–R12) — referência obrigatória nos commits
  das emendas de ADR e do PRP-MAP.
- **A instalar (R1):** PRP-ACE-TAGS com testes de regressão (tag nova aceita; formato
  antigo de `<gate_result>` rejeitado).
- **Proposta de follow-up (fora deste GOV):** avaliar gate de fact-check para ADRs que
  descrevem o tooling — ex.: checklist "todo ADR que afirma fato de código cita arquivo
  + linha verificada", impedindo reincidência da classe (C2).

## Área Afetada

`docs/architecture/` (ADRs 0002/0004/0005/0006, factory-evolution), `docs/prps/` (20 PRPs),
`docs/planning/PRP-MAP.md`, `.ace/scripts/validate-tags.py`, `.ace/scripts/llc_steps/`,
`.ace/scripts/initialize_session.py`, `.ace/scripts/finalize_session.py`,
`.ace/config/gates.json`, `AGENTS.md`, `llc-pipeline-design.md`, GOV-002, PRP-GOV-004.

## Validação Posterior

- [ ] Bloco 1 (R1–R3) concluído antes de qualquer commit de código do PRP-MAP
- [ ] `validate-tags.py` aceita `user_response`/`eval_metrics`/`task_completed` com testes verdes
- [ ] PRP-GRAPH-1A executado sem referência a `depends_on` inexistente
- [ ] PRP-GRAPH-1C executado sem refactor de assinatura do `KanbanBoardBuilder` (adapter)
- [ ] `PRP-MAP.md` com caminho crítico corrigido e PRP-GOV-004 referenciado
- [ ] Zero falhas de `validate-tags.py --coverage` em commits das Trilhas 0–3

## Status da Reincidência

0/3 PRPs do PRP-MAP executados sem reaparecimento de gap 🔴 desde a abertura (2026-08-05).
Transição para `closed` exige: Bloco 1 concluído + 3 PRPs do mapa executados sem novo
conflito de contrato detectado.

**Progresso (2026-08-05):** ✅ **Bloco 1 concluído** — R1 (PRP-ACE-TAGS), R2 (fonte do grafo
= ordem do REGISTRY), R3 (adapter `GraphPipelineDataSource`). ✅ **Bloco 2 concluído** —
R4 (tabela de derivação `StepStatus` + `GateItem.required` default true, PRP-WIZARD-1A §7.6),
R5 (ADR-0007: campo `prp` no `index.json` como fonte N2 — zero código, capacidade já existente),
R6 (caminho crítico via GRAPH-1A/1B; EVALS-F1 paralelo ao 1A), R7 (fail-fast anti
sessão-placeholder — GOV-002 `addressed`, bloqueio de WIZARD-1A removido), R8 (AGENTS.md
sanciona `UserDecisionWriter` append-only + `<eval_metrics>` via `finalize_session`;
ADR-0002 P2 e PRP-EVALS-F1 alinhados). ✅ **Bloco 3 concluído** — R9 (ADRs 0002/0004/0005/0006
movidos para `docs/architecture/adr/`; ADR-001→ADR-0001; todos os docs e templates de ADR
padronizados para 4 dígitos; path do factory-evolution corrigido (`docs/architecture/`) e
alignment v1.8.0→v1.9.0), R10 (`dependency-admission` declarado checklist de PR no AGENTS.md
Parte III — não gate de pipeline; enforcement via `--check-governance`), R11 (coexistência
`impact-analyzer.py`≠`GraphEngine.impact_of()` declarada e justificada no PRP-GRAPH-1B §1 e
ADR-0004 errata R11), R12 (narrativa de investimento ~12sem MVP vs ~24sem trilha completa
reconciliada em `factory-evolution.md` §4 e `PRP-MAP.md`).
Durante o R1 foi registrada a 3ª reincidência do GOV-002 (sessões órfãs durante `pytest`) —
removidas conforme controle; fix instalado no R7.
