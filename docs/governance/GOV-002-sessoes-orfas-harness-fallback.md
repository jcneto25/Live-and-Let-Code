# GOV-002: Sessões ACE criadas por caminhos não-operacionais

**Status**: addressed
**Data de abertura**: 2026-07-31
**Data de instalação**: 2026-08-05
**Data de fechamento**: (pendente — 3 PRPs sem reincidência após instalação)
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
- **Fail-fast (instalado em 2026-08-05, sessão 2026-08-05-004 — Decisão item 2):**
  - `initialize_session/session.py::is_placeholder_task()` — detecta sentinel
    (`Step N` literal, vazio, None)
  - `initialize_session/cli.py` — recusa com `exit 2` + mensagem pedindo `--task`
    real, **antes** de criar qualquer arquivo (camada determinística)
  - `llc_harness/session.py::session_start()` — mesma guarda antes de invocar o
    subprocesso; **removida** a manufatura `task or f"Step {step}"` (a causa raiz)
  - Evidência: `test_session_task_guard.py` (15 testes); suite completa após o fix
    criou **zero** órfãs (antes: 3 por execução)

## Área Afetada

.ace/sessions/, .ace/index.json, .ace/scripts/llc/cli.py, .ace/sessions/__pycache__

## Validação Posterior

Verificação de higiene (frontmatter-taxonomy, compatível com o schema de
`index.json` — que não armazena `project`):

```bash
python3 - <<'PY'
import json, re
for s in json.load(open('.ace/index.json'))['sessions']:
    t = open('.ace/sessions/'+s['file']).read()
    proj = re.search(r'project:\s*"([^"]*)"', t); proj = proj.group(1) if proj else '?'
    nd = len(re.findall(r'<file_delta>', t))
    st = re.search(r'status:\s*"(\w+)"', t); st = st.group(1) if st else '?'
    assert not (proj == '' and nd == 0 and st == 'in_progress'), s['file']
print('OK: 0 sessoes orfa-placeholder indexadas')
PY
```

Nenhuma sessão órfã-placeholder (`project: ""` + zero `<file_delta>` + `in_progress`
eterno) deve permanecer em `index.json`.

## Status da Reincidência

3 ocorrências documentadas:
1. 2026-07-31 11:08 (removida na sessão 31-001)
2. 2026-07-31 13:17 e 14:10 (descobertas na sessão 31-004)
3. **2026-08-05** — sessões `2026-08-05-004/005/006` criadas durante `pytest .ace/scripts/`
   (suite completa dispara o caminho `llm_fallback` do `llc.py` com defaults de docstring).
   Removidas na sessão 2026-08-05-003 conforme o controle deste GOV (Decisão item 1).
4. **2026-08-06** — sessões `2026-08-06-005/006` (`task: "tarefa"`, `project: ""`, zero actions)
   criadas fora do fix: o sentinel `is_placeholder_task` só pegava `"Step N"`/vazio, então
   `"tarefa"` passou. Removidas na sessão 2026-08-06-008 e o sentinel foi **endurecido**
   (ver *Mecanismo Instalado* — agora rejeita token-placeholder genérico case-insensitive
   via `_PLACEHOLDER_TOKENS`: `tarefa`, `task`, `smoke`, `todo`, `x`, `tbd`...).

A 3ª reincidência confirmou que o controle manual não bastava. O fix arquitetural
(Decisão item 2) foi **instalado em 2026-08-05** (ver *Mecanismo Instalado*).
A 4ª reincidência (08-06, `"tarefa"`) fechou a lacuna do sentinel: **endurecido
em 2026-08-06** (sessão 008) para tokens-placeholder genéricos, com testes
`test_session_task_guard.py` ampliados. **Concomitantemente, 12 sessões órfãs
históricas (07-07/07-10/07-27 + 08-06-005/006) foram removidas** (10 via `git rm`
+ 2 untracked), reconciliados `index.json` (drift `2026-08-05-018` → completed).
Contagem reiniciada: **0/3 PRPs sem nova sessão órfã desde 2026-08-06** —
transição para closed após 3 PRPs executados sem reincidência.
