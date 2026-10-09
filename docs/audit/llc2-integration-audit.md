# LLC2 Integration Audit

> **Última atualização: 2026-10-09** (sessão ACE `2026-10-09-009`, Fase 1 do
> plano `docs/llc2-complementacao-plano.md`). Este documento substitui o
> placeholder anterior, que afirmava incorretamente
> "Estado: Fase 1-5 complementadas. 248 testes verdes" — o estado real medido
> era F1/F2/F6 não concluídas e 230 testes (hoje 238). O plano manda ler o
> §0 dele antes de qualquer etapa; este arquivo agora reflete o mesmo estado
> medido, para não induzir o agente seguinte ao erro.

## 1. Pontos de integração

| Ponto | Local | Estado |
|---|---|---|
| Early Commitment v2 (classify) | `llc_harness/replay.py::agent_invoke` | ✅ ativo sob `LLC2_CLASSIFY` |
| Replay harness → Decision Engine (R-2, F1) | `llc_harness/replay.py::classify_v2_routing` + ramo `LLC2_REPLAY` | ✅ concluído 2026-10-09 (tarefas 1.3–1.7) |
| Verificação versionada pós-hit (tarefa 1.5) | `verify_replay_from_record` chamada em `replay_hit` | ✅ pós-hoc, nunca bloqueia o replay |
| Smart Skip impact_of-first (R-4, F2) | `llc_delta/report.py` | ❌ não iniciado — helpers não existem; usar `GraphEngine.impact_of()` (`llc_graph/engine.py:221`) |
| NodeMachine (R-3, F4) | `llc_harness/pipeline.py` (`LLC2_STATECHART`) | ✅ global, por decisão humana de 2026-10-09 (plano §5) |
| Capabilities tool-agnostic (R-6, F5) | `llc2/capabilities.py` | 🔶 só `claude-code`; `generate_permission_profile` existe mas não é chamada pelo pipeline; `detect_modified_file_violations` não existe |
| Baseline de métricas (R-7, F6) | `LLC2_BASELINE` | ❌ ausente (0 ocorrências) |

## 2. Estado por fase (medido em 2026-10-09)

| Fase | Estado | Evidência |
|---|---|---|
| F1 — R-2 replay→Engine | ✅ concluída | 8 testes novos em `.ace/scripts/llc_harness/tests/`; smoke GO §2.2: `replay_hit_rate` 100% (≥40%), `llm_fallback` 0, `no_classify` 0, parsing errors 0, campos versionados (`decision_id`/`input_hash`/`question_set_hash`/`policy_version`) em todos os `replay_hit` |
| F2 — R-4 impact_of-first | ❌ não iniciada | `should_use_semantic_impact`/`residual_impact`: 0 ocorrências |
| F3 — R-5 DecisionRecord | 🔶 parcial | infra `llc_trace` pronta; `agent_invoke` agora carrega campos versionados no `evidence` (tarefa 1.6); `policy_version`/`thresholds_hash`/`question_set.hash` como campos de 1ª classe em `_trace_early_commitment` continuam pendentes |
| F4 — R-3 NodeMachine | ✅ decidida | manter global (plano §5, decisão humana) |
| F5 — R-6 capabilities | 🔶 parcial | 8× `claude-code`; perfil não gerado no pipeline |
| F6 — R-7 baseline + auditoria | 🔶 parcial | auditoria = este documento; baseline não implementado |

## 3. Suítes de teste (2026-10-09)

```text
python -m pytest llc2_spec/test_invariants.py .ace/scripts/llc2/tests/ -q   → 183 passed (175 + 8 novos da F1)
(cd .ace/scripts && python -m pytest llc_replay/tests/test_verify.py llc_graph/tests/test_engine.py -q) → 55 passed
hook pre-commit → exit 0 · fitness functions 41/41
```

## 4. Flags

| Flag | Default | Escopo |
|---|---|---|
| `LLC2_CLASSIFY` | `1` | Early Commitment v2 |
| `LLC2_REPLAY` | `0` | Replay harness → Decision Engine (F1). Ligar `1` após validação em ambiente real |
| `LLC2_STATECHART` | `1` | NodeMachine global (decisão 2026-10-09) |
| `LLC2_BASELINE` | — | não implementado (F6) |

## 5. Divergências remanescentes

1. **Replay interno do classificador — RESOLVIDO via solução A (2026-10-09, sessão 012).** Causa raiz (sessão 010): `attempt_replay` (`llc_replay/verify.py:390-407`) exigia `(record.statechart).to` para **qualquer** kind, mas `_trace_classification` não gravava `statechart`/`hard_eval`/`jev`. Conserto: `_trace_classification` agora grava `statechart` sintético (`idle→classified`), `jev_result` (via `record_payload`), `hard_eval: {checks: []}`, `risk_class: R1` e `question_set` completo; `record_decision` ganhou os 4 params opcionais. Verificação (`attempt_replay`/`verify_replay`/`decide`) intacta — `_dict_to_decision_record` já lia os campos. Critério atendido: 2ª classificação `replayed: True`/`replay_hit`, Jev 1x em 4 chamadas. Pendências restantes: (a) records históricos nunca batem (sem insumos gravados); (b) `log_replay_attempt` segue sem chamadas em produção — tentativas invisíveis em `replay.jsonl` (follow-up de observabilidade).
2. F3: promover `policy_version`, `thresholds_hash` e `question_set.hash` a campos de 1ª classe no `record_decision` do early commitment.
3. Unificar `_derive_routing` com `decide()`: o caminho vivo de classificação deriva o routing por tabelas de política (`_derive_routing`), não por `decide()` — comentários em `llc_harness/replay.py` corrigidos em 2026-10-09-014 para refletir isso; a unificação em si é follow-up (muda semântica ao vivo).
4. F5/F6: `capability-control.md` segue placeholder (167 bytes); `LLC2_BASELINE` ausente.
