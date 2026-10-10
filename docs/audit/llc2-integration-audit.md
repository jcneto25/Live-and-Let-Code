# LLC2 Integration Audit

> **Última atualização: 2026-10-10** (sessão ACE `2026-10-10-008`, Fase 6 do
> plano `docs/llc2-complementacao-plano.md` — tarefa 7.3). Todas as fases
> F1–F6 concluídas (F2 com ressalva documentada). Números medidos, não
> estimados; comandos na §4.

## 1. Pontos de integração

| Ponto | Local | Estado |
|---|---|---|
| Early Commitment v2 (classify) | `llc_harness/replay.py::_agent_invoke_inner` via `classify_v2_routing` | ✅ ativo sob `LLC2_CLASSIFY=1` (default); replay interno do classificador funcional (solução A) |
| Replay harness → Decision Engine (R-2, F1) | `replay.py::classify_v2_routing` + ramo `LLC2_REPLAY` | ✅ concluído (tarefas 1.3–1.7); `verify_replay_from_record` pós-hit, nunca bloqueia |
| Verificação versionada pós-hit (1.5 + F3/3.3) | `find_matching_record(outcome="classify")` → record REAL; stub só em fallback | ✅ filtro `outcome=` corrige shadowing que matava o replay em fluxos reais |
| Smart Skip impact_of-first (R-4, F2) | `llc_delta/skip.py` (helpers) + `llc_delta/report.py` (portão) | 🔶 API de política testada, sem caller de produção (`report.py` é parser puro); guarda fail-closed ALWAYS_RUN no portão |
| DecisionRecord versionado (R-5, F3) | `replay.py::_trace_early_commitment`, `pipeline.py::_record_node_state`, `gates.py`, `verify.py` | ✅ config versionado + routing real + `evidence_refs`; records de estado sob `LLC2_RECORD=1`; dedup step.start/end |
| NodeMachine (R-3, F4) | `pipeline.py` (`LLC2_STATECHART`) | ✅ global, por decisão humana de 2026-10-09 (plano §5) |
| Capabilities tool-agnostic (R-6, F5) | `llc2/capabilities.py` + wiring em `pipeline.py::step_run` | ✅ mapas por cliente (claude exato; demais best-effort) + apply opt-in com backup `.bak` + detecção post-hoc warn-only com snapshot diff |
| Baseline de métricas (R-7, F6) | `replay.py::agent_invoke` (wrapper) | ✅ evento único `phase="invoke"` por chamada (latência/tokens/contadores 7.2 + `exit_code`); append-only em `baseline.jsonl`; default 0 sem impacto |
| Re-exports do harness | `llc_harness/__init__.py` | ✅ expõe `agent_invoke` (+ replay/classify); `llc/cli.py` importa sem chamar (re-export morto) |

## 2. `llc2_spec/` vs `.ace/scripts/llc2/` (marcadores F1–F7)

O pacote `scripts` deriva da spec por **adição** (verificado por `diff` em 2026-10-10):

| Artefato | Relação |
|---|---|
| `contracts.py` | scripts = spec + paths `config/` + campo `doc_judge_weights` + §15 `NodeMachine` (~+356 linhas). Núcleo de decisão idêntico |
| `decision-policy.v1.yaml` | scripts = spec + bloco `doc_judge_weights` (aditivo) |
| `jev_adapter.py` | difere (adaptadores de transporte por ambiente) |

| Marcador (PASSAGEM-4 §3) | Estado no scripts |
|---|---|
| F1 — Thresholds são dados, não literais | ✅ policy YAML + `thresholds_hash`; produção sem literais novos: `contracts.py` 5 linhas com `0.80/0.20/0.92` em ambos (3×`0.80` + 3×`0.20` ocorrências em ambos; `0.92` ×0 em produção — os ×14 do pacote são fixtures `FakeJev` em `tests/`, como o ×1 da spec em `test_invariants.py:66`). Comandos na §4 |
| F2 — `decide()` fecha o fail-open | ✅ `contracts.py:467` (`semantic_unavailable` → HUMAN_REQUIRED); docstring "Fail-closed" |
| F3 — Noul: direção antes de força | ✅ `contracts.py:411,488` |
| F4 — Classificação nunca descartada (§14) | ✅ rótulo sempre preservado (F1); `replay.py` não descarta por threshold |
| F5 — Regiões paralelas | ✅ `contracts.py:1033` (regiões ortogonais hard/semantic) |
| F6 — Assinatura uniforme de guard | ✅ `contracts.py:667` (`GuardContext`) |
| F7 — Replay verifica `input_hash` | ✅ `llc_replay/verify.py` compara antes de reproduzir (F3/3.3 confirma) |

## 3. Estado por fase (medido em 2026-10-10)

| Fase | Estado | Evidência |
|---|---|---|
| F1 — R-2 replay→Engine | ✅ concluída | 8 testes `llc_harness/tests/`; smoke GO §2.2: `replay_hit_rate` 100% (≥40%), `llm_fallback` 0, `no_classify` 0 |
| Solução A — replay interno do classificador | ✅ concluída | 2ª classificação `replayed: True`/`replay_hit`, Jev 1× em 4 chamadas; 4 testes `test_classifier_replay.py` |
| F2 — R-4 impact_of-first | ✅ concluída com ressalva | 22 testes; helpers puros + portão com guarda ALWAYS_RUN; **sem caller de produção** (GO §3.2 linha 1 não-exercível — registrado no plano) |
| F3 — R-5 DecisionRecord | ✅ concluída | 10 testes `test_decision_records.py`; GO §4.2 medido com `LLC2_RECORD=1`; exceção de compat do routing real registrada no plano |
| F4 — R-3 NodeMachine | ✅ decidida | manter global (plano §5, decisão humana) |
| F5 — R-6 capabilities | ✅ concluída + reparo pós-review | 30 testes (22 capabilities + 8 wiring); backup `.bak`, snapshot diff, fallback único `generic`, dedupes; mapas best-effort **não certificados** |
| F6 — R-7 baseline + R-1 auditoria | ✅ concluída + reparo pós-review | 26 testes `test_baseline_metrics.py` (incl. replay REAL ponta a ponta); evento único consolidado; contrato dict×tupla normalizado (item 8 das resolvidas); este documento (7.3) |

## 4. Suítes de teste (2026-10-10)

```text
(cd .ace/scripts && python -m pytest . -q --ignore=llc_evals) → 787 passed
python -m pytest llc2_spec/test_invariants.py -q                  → 73 passed
# §2 (F1–F7): derivação por adição + paridade de literais —
diff llc2_spec/contracts.py .ace/scripts/llc2/contracts.py        → só paths config/ + doc_judge_weights + §15 NodeMachine
diff llc2_spec/decision-policy.v1.yaml .ace/scripts/llc2/decision-policy.v1.yaml → só bloco doc_judge_weights
grep -c "0\.80\|0\.20\|0\.92" llc2_spec/contracts.py .ace/scripts/llc2/contracts.py → 5 = 5 (linhas)
grep -ro "0\.92" .ace/scripts/llc2/ --include="*.py" | grep -v "/tests/" | wc -l → 0 (produção; ×14 são fixtures)
```

Escopo: `llc_evals/` (113 testes) excluído — exige Jev real, indisponível no
sandbox (sem path de import até o código das fases; provado na F2). Nenhuma
falha no escopo; `test_verify.py` 20/20 intacto em todas as fases.

## 5. Flags

| Flag | Default | Escopo |
|---|---|---|
| `LLC2_CLASSIFY` | `1` | Early Commitment v2 |
| `LLC2_REPLAY` | `0` | Replay harness → Decision Engine (F1) |
| `LLC2_DELTA_IMPACT_FIRST` | `1` | impact_of-first (F2, recomendado) |
| `LLC2_RECORD` | `0` | Records de estado NodeMachine novos (F3; writes pré-existentes seguem `LLC_TRACE`, default ON) |
| `LLC2_STATECHART` | `1` | NodeMachine global (decisão §5) |
| `LLC2_NODEMACHINE_STEPS` | (opcional) | CSV de steps extras (F4, não usado — adoção global) |
| `LLC2_APPLY_CAPABILITY_PROFILE` | `0` | Aplica perfil por estado (F5; detecção post-hoc é always-on) |
| `LLC2_BASELINE` | `0` | Captura baseline métricas (F6) |

Todas as flags novas lidas **por chamada**, nunca congeladas no import.

## 6. Divergências

### 6.1 Resolvidas (com evidência)

1. **Replay interno do classificador** (sessões 010→012, solução A): `_trace_classification` grava `statechart` sintético + `jev_result` + `hard_eval` + `risk_class` + `question_set`; verificação intacta.
2. **Shadowing do replay** (F3): filtro `outcome=` em `find_matching_record`/`attempt_replay`; reproduzido (`reused False`, Jev 2×) antes do fix, com teste de regressão.
3. **GO × defaults** (F3/F5): tensões documentadas como notas de validação no plano (§4.2/§6.2) — GO medido sob flag ligada, não no default.
4. **Clobber de settings** (reparo F5): `write()` com backup `.bak` + no-op idêntico + disclose §7 do doc.
5. **Dirty-tree FP** (reparo F5): snapshot diff antes/depois; **fallback triplo** unificado em `generic`; mapas/path deduplicados.
6. **Rastreabilidade F2** (sessão 018): deltas/task_completed/gate em sessão de reparo (016 imutável); coverage 9/9.
7. **Colisão de ID no TASKS.md** (REVERT-F3): `F3`→`LLCC-F3`; `TASKS.md:218` restaurado ao git-truth.
8. **Contrato dict×3-tupla no replay** (reparo pós-review F6): `deterministic_replay` retornava `{"status": "success"}` (`execute.py:100`) e `step_run` desempacotava 3-tupla (`pipeline.py:405`) → `ValueError` em todo replay bem-sucedido (pré-existente desde `ce17b18`). Fix: normalização no site `return deterministic_replay(...)` do inner (always-run) para `("replay:<id>", 0, None)` + teste de regressão com replay REAL (`steps: []`) atravessando `agent_invoke` e `step_run` (flag on e off). Métricas 7.2 corrigidas junto: `calls_jev` só quando o Jev roda, `jev_calls_avoided` computado, `tokens_out=0` sem output, evento único (fim da dupla contagem).

### 6.2 Remanescentes (follow-ups abertos)

1. Records históricos de classificação nunca batem em replay (sem insumos gravados) — aceito.
2. `log_replay_attempt` (`verify.py:443`) segue sem chamadas em produção — tentativas invisíveis em `replay.jsonl`.
3. `_derive_routing` × `decide()` não unificados (`replay.py:160-163`, divergência doc/código registrada).
4. Mapas best-effort `opencode`/`codex`/`cursor` não certificados — requer certificação manual.
5. F2 sem caller de produção — wiring aguarda gatilho semântico por step com `changed_nodes`.
6. Atribuição pós-agente imperfeita: arquivo tocado antes E pelo agente ainda sinaliza (fail-closed, documentado).
