# GOV-002: Sessões ACE criadas por caminhos não-operacionais

**Status**: open
**Data de abertura**: 2026-07-31
**Data de instalação**: (pendente)
**Data de fechamento**: (pendente)
**Step de origem**: 11.4 (auditoria contínua do pacote GOV)
**PRP relacionado**: PRP-GOV-004

## Sintoma

Sessões `.ace/sessions/YYYY-MM-DD-NNN.md` criadas com `task_context: "Step 0.5"`,
`project: ""`, `tags: []` — nunca trabalhadas, nunca finalizadas (`status: in_progress`
permanente). Não refletem trabalho humano ou de agente.

## Contexto

Observado 3 vezes no mesmo dia (2026-07-31) em horários: 11:08 (removida na sessão
31-001), 13:17 e 14:10 (descobertas na sessão 31-004). Os timestamps coincidem
exatamente com eventos `llm_fallback` em `.ace/logs/replay.jsonl` (13:17:12.2,
14:10:38.9), indicando caminho de fallback do harness que invoca `initialize_session.py`
com argumentos default do exemplo da docstring.

## Classe de Falha

Falha Estrutural (recorrente) — componente não-operacional grava em caminho de dados
críticos (`.ace/sessions/` é fonte de verdade do ACE e entrada de `validate-tags.py`,
`gov-tools.py check-recurrence`, métricas de handoff).

## Impacto

Alto — sessões falsas poluem `index.json`, quebram a cadeia `prev_session`, fazem
`check-recurrence` ler `blockers` de sessões vazias, e distorcem `governance-metrics.py`
(se usasse contagens de sessões).

## Evidência

- `git status` em 31/07 15:16: `?? .ace/sessions/2026-07-31-002.md`, `?? 2026-07-31-003.md`
- `replay.jsonl` linhas 11-12: fallbacks nos mesmos timestamps das criações
- Ambas `status: in_progress`, `llc_step: 0.5`, sem actions delas

## Causa Estrutural

`llc.py` (caminho `llm_fallback`) invoca `initialize_session` com argumentos de
exemplo quando a classificação falha. `initialize_session` não valida se `--task`
é um exemplo de docstring/sentinel, nem se a sessão resultante é "real"
(mínimo: task não-placeholder + projeto definido).

## Decisão

Ambos — controle determinístico agora, arquitetural na próxima wave:
1. (controle, este commit) Sessões órfãs identificadas são removidas com nota no
   commit e na sessão ativa; padrão de detecção documentado.
2. (arquitetural, próxima wave) `llc.py` llm_fallback deve **não** chamar
   `initialize_session` com defaults de docstring; deve falhar explicitamente
   pedindo `--step`/`--task` reais.

## Mecanismo Instalado

- Remoção manual documentada (compromisso de higiene, precedente em f90894b)
- Taxonomia canônica: sessão órfã = `project: ""` + `task_context` igual a
  `Step N` literal + zero actions + zero tags

## Área Afetada

.ace/sessions/, .ace/index.json, .ace/scripts/llc/cli.py, .ace/sessions/__pycache__

## Validação Posterior

`python -c "import json; d=json.load(open('.ace/index.json')); assert all(s['project'] for s in d['sessions'])"`
— toda sessão registrada deve ter `project` não-vazio.

## Status da Reincidência

2 ocorrências documentadas neste GOV (11:08 e 13:17/14:10). Transição para closed
exige 3 PRPs sem nova sessão órfã.
