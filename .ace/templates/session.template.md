---
session_id: "{{session_id}}"
llc_step: {{llc_step}}
project: "{{project}}"
prev_session: "{{prev_session_id}}"
---

## Contexto

{{#if prev_context_seed}}
<context_seed>
{{prev_context_seed}}
</context_seed>
{{else}}
Primeira sessão do projeto.
{{/if}}

## Ações

<action_log>
</action_log>

## Aprendizados

<!-- <learning_point priority="high">...</learning_point> -->

## Gates

<!-- <gate_result step="N" decision="approved" reviewer="...">...</gate_result> -->

## Bloqueadores

<!-- <blocker resolved="false">...</blocker> -->

## Encerramento

<context_seed>
state: [preencher no encerramento]
pending: [preencher no encerramento]
blockers: [preencher no encerramento]
next_action: [preencher no encerramento]
</context_seed>

---
status: completed
duration_min: {{duration}}
files_touched: []
