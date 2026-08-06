# ADR-0005: Eval Harness — Medição de Eficiência e Corretude por Etapa do Pipeline

**Arquivo:** `docs/architecture/adr/ADR-0005-eval-harness.md`

```yaml
---
adr: "0005"
title: "Eval Harness — Medição de Eficiência e Corretude por Etapa do Pipeline"
status: accepted
date: 2026-08-05
last_updated: 2026-08-05
deciders:
  - jcneto25
supersedes: null
related:
  - ADR-0002   # Kanban exibe scores por card
  - ADR-0004   # Nós do grafo carregam métricas de eval
  - "issue #22"
tags: [evals, llm-as-judge, metrics, efficiency, correctness, regression, observability]
compliance:
  fitness_functions: [arch, clean-code]
  gates: [5, 9a, 10.8, 11.3]
---
```

> **Relação com outros ADRs:** este ADR é **transversal** e **consome** as fundações dos ADRs anteriores. Ele alimenta o Kanban (ADR-0002) com scores por card, os nós do grafo (ADR-0004) com métricas de eficiência, e os gates humanos com avaliações prévias. Não é pré-requisito de nenhum ADR futuro, mas **enriquece** todos.

---

## 1. Contexto

### 1.1 Situação Atual — Sementes de Eval Fragmentadas

O LLC já possui múltiplos mecanismos que avaliam qualidade, porém **fragmentados, reativos e sem medição de eficiência**:

| Mecanismo Existente | O Que Avalia | Limitação |
|---|---|---|
| Fitness Functions (40 checks) | Qualidade de código/arquitetura | Só código; não mede tokens nem corretude semântica |
| LLM self-validation (8 checks) | Geração do agente | Binário (pass/fail), sem score agregado |
| Gates humanos | Artefatos | Subjetivo, sem métrica, sem histórico comparável |
| consistency-check / prp-verify | Consistência de PRPs | Específico, não agrega em score |
| code-health.py | Saúde do código + coverage | Não cobre etapas documentais |
| Sessões ACE | Contexto + resultado | Não captura tokens/custo |

**O gap:** nenhum mecanismo responde *"qual a eficiência desta etapa?"*. Não há agregação temporal (regressão), nem relação **custo ↔ qualidade**, nem comparação entre execuções. Os evals existem como *gates discretos*, não como *sistema de medição contínua*.

### 1.2 Vantagem Estrutural do LLC

Diferente de sistemas sem disciplina de execução, o LLC já tem **cada step como unidade mensurável**: sessões ACE com artefatos, gates e (futuramente) tokens. Isso torna a instrumentação significativamente mais barata do que seria em outros contextos.

### 1.3 Forças em Jogo

| Força | Direção |
|---|---|
| **Tool-agnostic** | Captura de tokens não pode acoplar a um cliente de IA específico |
| **Integridade ACE** | Métricas não podem violar escritores sancionados |
| **Corretude heterogênea** | Steps documentais, arquiteturais e de código exigem evaluators distintos |
| **Custo dos próprios evals** | LLM-as-judge consome tokens; evitar overhead excessivo |
| **Não bloquear o pipeline** | Eval é informativo, não gate bloqueante (exceto quando integrado a gates) |
| **Reaproveitamento** | Fitness/testes/consistency já existem; agregar, não recriar |

### 1.4 Escopo

Este ADR define o **Eval Harness**: instrumentação de custo, evaluators por tipo de step, agregação de scores com detecção de regressão, e reporting integrado. Não cobre otimização automática de prompts (futuro) nem integração com plataformas externas de eval (opcional, posterior).

---

## 2. Decisão

Implementar o **Eval Harness** — um sistema de medição contínua que, para cada etapa do pipeline, responde: *"Atingiu a qualidade esperada? Quantos tokens custou? Está melhor ou pior que antes?"* O harness é organizado em **4 camadas** (Instrumentação → Evaluators → Agregação → Reporting) e avalia três dimensões por etapa: **Corretude**, **Eficiência** e **Efetividade**.

### 2.1 Princípios de Design (não negociáveis)

| # | Princípio |
|---|---|
| **P1** | **Medir antes de otimizar** — instrumentação de custo é o alicerce |
| **P2** | **Reaproveitar antes de inventar** — agregar mecanismos existentes |
| **P3** | **Corretude é heterogênea** — evaluator específico por tipo de step |
| **P4** | **Regressão > comparação absoluta** — comparar step contra seu próprio baseline |
| **P5** | **Tool-agnostic** — captura com fallback em múltiplos níveis |
| **P6** | **Integridade ACE preservada** — métricas append-only, sem tocar frontmatter |
| **P7** | **Eval não bloqueia** — é assíncrono e informativo; integra-se a gates sem substituí-los |

### 2.2 As Três Dimensões de Avaliação

| Dimensão | Pergunta | Como Medir |
|---|---|---|
| **Corretude** (Quality) | "O output atende ao esperado?" | LLM-as-judge + rubric + fitness + testes |
| **Eficiência** (Cost) | "Quanto custou produzir?" | Tokens in/out, latência, custo $ |
| **Efetividade** (Value) | "Valeu a pena?" | Corretude ÷ custo; taxa de aprovação de primeira |

A dimensão central desta iniciativa — **tokens vs corretude** — é a **Efetividade**: não basta ser correto nem barato; é ser correto *para aquele custo*.

### 2.3 Fórmulas de Score

```
QualityScore(step)      ∈ [0,100]                      # corretude do artefato
TokenCost(step)         = tokens_in + tokens_out
EfficiencyScore(step)   = QualityScore / log10(TokenCost)   # qualidade por token
FirstPassRate(step)     = gates_aprovados_1a_vez / total_gates
ReworkWaste(step)       = tokens_gastos_em_retries / TokenCost
```

**Decisão crítica (D6):** `EfficiencyScore` **não compara steps diferentes entre si** — um step de arquitetura é inerentemente mais complexo que um glossário. Compara-se **o mesmo step contra seu baseline histórico**. Regressão é a métrica que importa (P4).

### 2.4 Arquitetura em 4 Camadas

```
┌────────────────────────────────────────────────────────────┐
│ 4. REPORTING / DASHBOARD                                     │
│    Kanban (ADR-0002) · Eval Report · Pareto · Regressão     │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────┐
│ 3. EVAL AGGREGATOR                                           │
│    QualityScore · EfficiencyScore · FirstPassRate            │
│    Baselines · detecção de regressão · ranking               │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────┐
│ 2. EVALUATORS (roteados por tipo de step)                    │
│    DocJudge (LLM-as-judge+rubric) · ArchEvaluator            │
│    CodeEvaluator (testes+fitness) · EfficiencyMeter (tokens) │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────┐
│ 1. INSTRUMENTATION                                           │
│    Captura tokens_in/out, artefatos, retries, duração        │
│    Hooks nas sessões ACE + logs dos clientes de IA           │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────┐
│ GOLDEN DATASETS / BASELINES  (.ace/evals/golden/, baselines) │
└────────────────────────────────────────────────────────────┘
```

### 2.5 Camada 1 — Instrumentação de Custo

Sem capturar tokens, nenhuma análise de eficiência é possível. Como o LLC é tool-agnostic e cada cliente expõe tokens de forma diferente, define-se **fallback em 3 níveis**:

| Nível | Fonte | Precisão |
|---|---|---|
| 1 | Log nativo do cliente (`.claude/`, logs do Codex) | Alta |
| 2 | Parsing de saída estruturada (usage reportado pelo agente) | Média |
| 3 | Estimativa por tokenizer sobre prompt+output | Baixa (fallback) |

Cada sessão ACE recebe um bloco de métricas **append-only** (mesmo padrão das tags `<user_response>` do ADR-0002), sem tocar o frontmatter:

```yaml
<eval_metrics timestamp="2026-08-05T10:00:00">
  step: "5"
  tokens_in: 12000
  tokens_out: 3500
  total_tokens: 15500
  cost_usd: 0.08
  duration_s: 45
  retries: 0
  source: "claude-log"        # nível 1/2/3
</eval_metrics>
```

### 2.6 Camada 2 — Evaluators por Tipo de Step

Não existe evaluator universal. O harness **roteia cada step para o evaluator adequado**:

| Categoria | Exemplos de Steps | Evaluator |
|---|---|---|
| **Documental** | 0.5 Visão, 1 Specs, 2 PRDs, 3 PRPs | `DocJudge` (LLM-as-judge + rubric) |
| **Arquitetural** | 5, 5a–5d, ADRs | `ArchEvaluator` (fitness arch + ADR completeness) |
| **Código** | 11 Execução, PRPs | `CodeEvaluator` (testes + fitness + coverage) |
| **Testes** | 9, 10.8 | `CodeEvaluator` (coverage + consistência) |
| **UX/Design** | 7, 7a | `DocJudge` (rubric de heurísticas) |

### 2.7 LLM-as-Judge para Steps Documentais

Para artefatos subjetivos, a prática padrão de mercado é **LLM-as-judge com rubric estruturado**: um LLM avalia o artefato contra critérios explícitos, retornando scores por dimensão.

- Rubrics são **arquivos YAML versionados** (um por step), com dimensões, pesos e critérios.
- O judge é instruído a retornar **apenas JSON** (evita saída livre e instável).
- O judge recebe o artefato **e os artefatos de origem** (upstream) para checar rastreabilidade.
- **Amostragem humana** valida periodicamente os judgments (calibração).

**Restrição de custo (P7/D10):** o judge roda apenas em pontos de gate ou por amostragem, não a cada geração, para não inflacionar o custo do pipeline.

### 2.8 Code Evaluator — Agregação do Existente

Para steps de código, o evaluator **agrega mecanismos já existentes** num score único, sem recriá-los (P2):

```
CodeQuality = w1·pass_rate(testes) + w2·fitness_score(40 checks)
            + w3·coverage + w4·consistency_check
```

### 2.9 Camada 3 — Agregação, Baselines e Regressão

- **Baselines:** cada step mantém um baseline histórico (média móvel de `QualityScore` e `TokenCost`) em `.ace/evals/baselines/`.
- **Regressão:** cada run compara-se ao baseline do **mesmo step**; deltas negativos além de um limiar disparam alerta.
- **Ranking:** steps são ordenados por `EfficiencyScore` e `ReworkWaste` para identificar gargalos de custo.

#### Política de Warm-up de Baseline

O LLC não possui dados históricos de tokens ou quality scores ao iniciar o Eval Harness. Sem dados suficientes, alertas de regressão produziriam ruído e falsas detecções. A política é:

| Fase | Condição | Comportamento |
|---|---|---|
| **Coleta** | `run_count < N_MIN` (default: `5`) | Dados coletados, baseline calculado em modo observação. **Nenhum alerta de regressão emitido.** |
| **Warm-up ativo** | `N_MIN ≤ run_count < N_STABLE` (default: `5–10`) | Alertas emitidos com tag `[baseline-unstable]` — informativo, não bloqueante. |
| **Baseline estável** | `run_count ≥ N_STABLE` (default: `10`) | Alertas normais. Baseline considerado confiável. |

**Decisão D11:** `N_MIN=5` e `N_STABLE=10` são os defaults, **configuráveis** via `.ace/config/gates.json → evals.baseline_warmup_min` e `evals.baseline_warmup_stable`. O arquivo de baseline persiste o `run_count` por step.

**Tratamento de dados por nível de precisão (resolve ambiguidade de `EfficiencyScore`):**

Dados coletados via nível 3 (estimativa por tokenizer) têm precisão ~70–80% vs. nível 1 (log nativo). Misturar os dois níveis no mesmo baseline distorce comparações. A política é:

- O campo `source` do `<eval_metrics>` é persistido junto ao baseline.
- `EfficiencyScore` **só compara runs do mesmo nível** entre si (nível 1 vs. nível 1; nível 3 vs. nível 3).
- Runs de nível 3 recebem tag `[precision: estimated]` no relatório — não são excluídos, mas identificados.
- Quando um step migra de nível 3 para nível 1 (ex.: cliente de IA adicionado), o baseline é **resetado** e o warm-up recomeça.

**Formato do arquivo de baseline:**
```yaml
# .ace/evals/baselines/step-5.yaml
step: "5"
run_count: 7
baseline_phase: "warmup"       # collecting | warmup | stable
warmup_config:
  n_min: 5
  n_stable: 10
by_precision_level:
  level_1:
    run_count: 3
    quality_score_avg: 84.2
    token_cost_avg: 14800
    efficiency_score_avg: 20.1
  level_3:
    run_count: 4
    quality_score_avg: 81.0
    token_cost_avg: 15200       # estimativa — menor precisão
    efficiency_score_avg: 19.4
```

### 2.10 Camada 4 — Reporting e Integração

| Consumidor | O Que Recebe |
|---|---|
| **Kanban (ADR-0002)** | `QualityScore` e custo por card; `REWORK` ganha `ReworkWaste` |
| **Graph (ADR-0004)** | Métricas de eval por nó; `critical_path` pode ponderar eficiência |
| **Gates humanos** | Eval **pré-gate** transforma "revisão cega" em "revisão informada por score" |
| **code-health.py** | Relatório de eval agregado ao relatório de saúde existente |

> **Integração com gates:** os evals rodam **antes** do gate e apresentam ao humano um resumo (`QualityScore=86, first_pass=true, custo=$0.08`). O humano continua decidindo (human-in-control), agora com dados.

### 2.11 Estrutura de Arquivos

```
.ace/scripts/llc_evals/                 # NOVO pacote
├── __init__.py
├── instrument.py                       # captura tokens/custo (3 níveis)
├── evaluators/
│   ├── doc_judge.py                    # LLM-as-judge + rubric
│   ├── arch_evaluator.py               # fitness arch + ADR completeness
│   ├── code_evaluator.py               # testes + fitness + coverage
│   └── efficiency_meter.py             # tokens, custo, duração
├── rubrics/                            # critérios por step (YAML versionados)
│   ├── rubric-step-2-prd.yaml
│   ├── rubric-step-5-arch.yaml
│   └── ...
├── aggregate.py                        # scores, baselines, regressão
├── report.py                           # eval report (Markdown/JSON)
└── tests/
.ace/evals/                             # dados (gerados)
├── golden/                             # golden datasets por step
├── baselines/                          # baseline histórico por step
└── results/                            # resultados de cada run
```

**Dependência (DIP):** `llc_evals` lê de `.ace/` e artefatos; não muta sessões (apenas append de `<eval_metrics>`); é consumido por `llc_wizard` (projeções) mas não depende dele.

### 2.12 Decisões Vinculantes

| # | Decisão | Valor |
|---|---|---|
| **D1** | Persistência de métricas | Append-only em sessões ACE (`<eval_metrics>`) + `.ace/evals/` |
| **D2** | Captura de tokens | Fallback em 3 níveis (log → parsing → estimativa), registrando `source` |
| **D3** | Roteamento de evaluators | Taxonomia por tipo de step (documental/arquitetural/código/teste/UX) |
| **D4** | Steps documentais | LLM-as-judge + rubric YAML versionado, saída JSON-only |
| **D5** | Steps de código | Agregar testes + fitness + coverage + consistency (não recriar) |
| **D6** | Comparação de eficiência | Apenas contra baseline do **mesmo step**, nunca entre steps |
| **D7** | Métrica primária | Regressão temporal (qualidade e custo vs baseline) |
| **D8** | Integração com gates | Eval roda **pré-gate** e informa o humano; não substitui a decisão |
| **D9** | Implementação | Tool-agnostic própria (Python); sem framework externo de eval |
| **D10** | Custo do judge | Roda em gates/amostragem; validação humana periódica dos judgments |
| **D11** | Warm-up de baseline | `N_MIN=5` execuções antes de alertar; `N_STABLE=10` para baseline confiável; configurável em `gates.json` |
| **D12** | Separação por nível de precisão | `EfficiencyScore` só compara runs do mesmo nível (1, 2 ou 3); baseline resetado ao migrar de nível |

---

## 3. Consequências

### 3.1 Positivas

- **Visibilidade de custo:** tokens e $ por step, antes inexistentes.
- **Corretude mensurável:** artefatos documentais ganham score objetivo via rubric.
- **Reaproveitamento:** fitness/testes/consistency viram componentes de um score unificado.
- **Detecção de regressão:** degradação de qualidade ou eficiência é alertada cedo.
- **Gates informados:** humano decide com dados, não às cegas.
- **Base para otimização:** ranking de steps ineficientes guia melhorias de prompt/skill.
- **Integração natural:** Kanban e Graph ganham métricas sem mudar suas UIs.

### 3.2 Negativas / Custos

- **Overhead de instrumentação:** capturar tokens exige adaptação por cliente de IA.
- **Custo do próprio judge:** LLM-as-judge consome tokens (mitigado por amostragem, D10).
- **Subjetividade residual:** mesmo com rubric, judgments podem variar (mitigado por validação humana).
- **Nova superfície de teste:** pacote `llc_evals` exige cobertura adequada.
- **Risco de over-metricação:** coletar métricas sem decisão associada gera ruído.

### 3.3 Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Capturar tokens é tool-dependent | Fallback em 3 níveis (D2); registrar `source` |
| Judge instável/subjetivo | Rubric estruturado + JSON-only + amostragem humana (D4/D10) |
| Eval custa tokens | Rodar só em gates/amostragem; cache de judgments |
| Não-determinismo dos outputs | Múltiplos runs quando crítico; média + variância |
| Comparar steps incomparáveis | Eficiência só contra baseline do mesmo step (D6) |
| Métricas sem uso | Cada métrica deve ter uma decisão associada (P1) |

---

## 4. Alternativas Consideradas

| Alternativa | Descrição | Motivo da Rejeição |
|---|---|---|
| **Adotar plataforma externa de eval** (Braintrust, LangSmith) | SaaS de evals | Viola tool-agnostic e privacidade; lock-in; pode vir como exportador depois |
| **Avaliar tudo com LLM-as-judge** | Judge universal | Inadequado para código (testes são mais objetivos e baratos) |
| **Avaliar só código (fitness)** | Manter apenas fitness | Deixa etapas documentais sem medição de corretude |
| **Comparar eficiência entre steps** | Ranking absoluto entre steps | Injusto (complexidades diferentes); rejeitado em favor de baseline por step (D6) |
| **Eval como gate bloqueante** | Bloquear pipeline se score baixo | Viola P7; eval informa, humano decide |
| **Métricas ad-hoc por skill** | Cada skill define suas métricas | Sem agregação/comparabilidade; rejeitado em favor de taxonomia unificada |
| **Sem instrumentação de tokens** | Medir só qualidade | Impossibilita a análise de efetividade (objetivo central) |

---

## 5. Compliance

### 5.1 Fitness Functions

- **Architecture:** `llc_evals` não muta sessões além do append de `<eval_metrics>`; projeções são puras.
- **Clean Code:** funções < 50 linhas; evaluators coesos; sem god-classes.
- **Deep Clean (CQS):** evaluators são queries (não mutam estado); `aggregate` é função pura.

### 5.2 Gates Aplicáveis

| Gate | Aplicação |
|---|---|
| Gate 5 | Arquitetura do Eval Harness documentada neste ADR |
| Gate 9a (TDD) | Todo módulo segue RED → GREEN → REFACTOR |
| Gate 10.8 | Cobertura de testes adequada em `llc_evals` |
| Gate 11.3 | `fitness-functions.py --all --strict` verde |

### 5.3 Testes Obrigatórios (TDD)

**`instrument.py`:** captura em cada um dos 3 níveis; fallback quando log ausente; bloco `<eval_metrics>` bem-formado.

**`evaluators/`:**
- `doc_judge`: dado artefato + rubric, retorna JSON com scores por dimensão; agrega pelos pesos.
- `code_evaluator`: agrega pass_rate + fitness + coverage corretamente.
- `efficiency_meter`: calcula `TokenCost` e `EfficiencyScore` corretamente.

**`aggregate.py`:**
- `EfficiencyScore` compara apenas contra baseline do mesmo step.
- Regressão detectada quando delta negativo excede limiar.
- `FirstPassRate` e `ReworkWaste` calculados corretamente.
- **Warm-up:** nenhum alerta emitido se `run_count < N_MIN`.
- **Warm-up ativo:** alertas com tag `[baseline-unstable]` se `N_MIN ≤ run_count < N_STABLE`.
- **Separação por nível:** `EfficiencyScore` só compara runs do mesmo nível de precisão.
- **Reset ao migrar de nível:** baseline resetado quando `source` muda de nível 3 para nível 1.

**Determinismo:** mesma entrada → mesmo score (fixar seeds/entradas nos testes).

---

## 6. Roadmap de Entrega

| Fase | Entrega | Valor | Risco |
|---|---|---|---|
| **F1 — Instrumentação** | Capturar tokens/custo/duração por sessão ACE | Custo por step visível | Baixo |
| **F2 — Code Evaluator** | Agregar testes+fitness+coverage em `CodeQuality` | Score único de código | Baixo |
| **F3 — DocJudge** | LLM-as-judge + rubrics para steps documentais | Corretude de artefatos | Médio |
| **F4 — Baselines + Regressão** | Golden datasets + detecção de degradação | Proteção contra regressão | Médio |
| **F5 — Pareto + Otimização** | Dashboard custo×qualidade; ranking de ineficiência | Melhoria contínua | Médio |

**Entrega mínima de valor (F1+F2):** em ~2 semanas obtém-se *custo por step* e *score de qualidade de código*, sem depender de LLM-as-judge.

---

## 7. Métricas de Sucesso

| Categoria | Métrica | Meta |
|---|---|---|
| Técnica | Cobertura de `llc_evals` | ≥ 85% |
| Técnica | Determinismo dos evaluators | 100% (mesma entrada → mesmo score) |
| Adoção | Steps com custo mensurado | 100% (após F1) |
| Qualidade | Correlação judge↔humano | ≥ 0,8 (validação por amostragem) |
| Valor | Regressões detectadas antes do gate | ≥ 90% |
| Valor | Redução de ReworkWaste | −20% em 3 meses |

---

## 8. Anexos

### 8.1 Exemplo de Rubric (Step 2 — PRD)

```yaml
# .ace/scripts/llc_evals/rubrics/rubric-step-2-prd.yaml
step: "2"
artifact: "PRD"
dimensions:
  - name: completude
    weight: 25
    criterion: "Todas as seções do template de PRD estão preenchidas?"
  - name: rastreabilidade
    weight: 25
    criterion: "Cada requisito traça até um módulo da Visão (Step 0.5)?"
  - name: testabilidade
    weight: 20
    criterion: "Os requisitos são verificáveis e mensuráveis?"
  - name: clareza
    weight: 15
    criterion: "Linguagem não ambígua, sem contradições internas?"
  - name: alinhamento_negocio
    weight: 15
    criterion: "Reflete os objetivos da Visão Estratégica?"
scoring: "0-100 por dimensão, agregado pelos pesos"
```

### 8.2 Prompt do Judge (esqueleto)

```
Você é um avaliador técnico rigoroso. Avalie o artefato contra a rubrica.
Para cada dimensão, atribua 0-100 e justifique em 1 frase.
Retorne APENAS JSON: {"<dimensao>": {"score": X, "reason": "..."}, ...}

[RUBRICA]
{rubric_yaml}

[ARTEFATO A AVALIAR]
{artifact_content}

[ARTEFATOS DE REFERÊNCIA / CONTEXTO UPSTREAM]
{upstream_artifacts}
```

### 8.3 Resultado por Step

```yaml
# .ace/evals/results/2026-08-05-step-5.yaml
step: "5"
run_id: "2026-08-05-001"
correctness:
  quality_score: 86
  judge: "arch_evaluator"
  first_pass: true
  retries: 0
efficiency:
  tokens_in: 12000
  tokens_out: 3500
  total_tokens: 15500
  cost_usd: 0.08
  duration_s: 45
effectiveness:
  efficiency_score: 18.9          # 86 / log10(15500)
  fitness_pass: "38/40"
baseline_comparison:
  quality_delta: +3
  token_delta: -1200
  regression: false
```

### 8.4 Boas Práticas de Mercado — Referência

| Boa Prática | Ferramentas de Referência | Aplicação no LLC |
|---|---|---|
| LLM-as-judge | Braintrust, DeepEval, LangSmith | Steps documentais |
| Rubrics estruturados | Braintrust, HumanLoop | Critérios por step |
| Golden datasets | OpenAI Evals, Promptfoo | Regression de skills |
| Pass@k | HumanEval, lm-eval-harness | Código |
| Regression testing | LangSmith, Promptfoo | Degradação temporal |
| Cost tracking | Helicone, LangSmith | Tokens/custo por step |
| Human eval sampling | Scale AI, Argilla | Calibrar o judge |
| Pareto frontier | (análise custom) | Custo×qualidade |

> Estas ferramentas são **referência de padrões**, não dependências (D9).

---

## 9. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-05 |
| claude | Co-autor da especificação | 2026-08-05 |

**Status:** `accepted`
**Dependências:** ADR-0002 (Kanban como consumidor) · ADR-0004 (Graph como consumidor)
**Próximo passo sugerido:** Quebrar a **Fase 1 (Instrumentação)** em tasks TDD granulares, ou gerar a issue de implementação correspondente (padrão `ready-for-agentSpec`).

---
