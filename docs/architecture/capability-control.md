# Capability Control

**Status:** implementado (F5/R-6, `llc2/capabilities.py` + wiring em `llc_harness/pipeline.py`).
**Tese:** prevenção via perfil de permissão por estado + detecção post-hoc como rede de segurança.

## 1. Limitação fundamental (leia primeiro)

O harness invoca o agente como **subprocess CLI** (`agent_invoke` via STDIN).
Um subprocess **não vê as tool calls** do agente — não há como interceptar,
autorizar ou bloquear uma chamada de ferramenta em tempo real.

Consequência: **prevenção é limitada por construção**. Nenhum perfil,
matriz ou guarda neste repositório impede de verdade um agente de chamar
uma tool. O que o Capability Control entrega de fato:

| Camada | Mecanismo | Força |
|---|---|---|
| Prevenção (best-effort) | Perfil de permissão por estado (allow/deny) escrito para o cliente | Advisory — o cliente pode ignorar |
| Detecção (real) | Verificação post-hoc sobre diff + zonas após o agente | Determinística — violação vira warning auditável |

## 2. Abordagem adotada

1. **Perfil por estado (prevenção):** a cada step com NodeMachine, o estado
   atual mapeia para capabilities (`CAPABILITY_MATRIX`), capabilities para
   tool calls do cliente, e o perfil é escrito no caminho do cliente —
   **apenas com `LLC2_APPLY_CAPABILITY_PROFILE=1`** (default `0`, opt-in:
   escrever settings do cliente é invasivo).
2. **Verificação post-hoc (detecção):** após o agente, `git diff` + zonas
   🔴 sinalizam modificações em arquivos vermelhos. Roda **sempre**
   (independente de flags), é **warn-only** e nunca bloqueia o pipeline
   (editar zona vermelha é rotina legítima — ex.: este próprio repo).

## 3. Clientes suportados

| Cliente (detectado) | Id de mapa | Vocabulário | Destino do perfil |
|---|---|---|---|
| `claude` | `claude-code` | Canônico, exato (`Read`/`Write`/`Bash`/…) | `.claude/settings.local.json` (formato nativo) |
| `opencode` | `opencode` | Best-effort minúsculo (`read`/`write`/`bash`/…) | `.llc2/permissions/opencode.json` (advisory) |
| `codex` | `codex` | Best-effort minúsculo genérico | `.llc2/permissions/codex.json` (advisory) |
| `cursor` | `cursor` | Best-effort minúsculo genérico | `.llc2/permissions/cursor.json` (advisory) |
| outros/`None` | `generic` | Canônico (fallback único, `client_map: generic`) | `.llc2/permissions/generic.json` (advisory) |

Detecção: `llc_harness.replay.detect_agent_client()` (`LLC_AGENT_CLI` ou PATH);
normalização: `llc2.capabilities.normalize_client_id()`.

## 4. Quando vira apenas detecção

- Cliente sem mapa próprio (`generic`) ou sem formato de settings conhecido:
  o perfil é advisory (JSON genérico que nenhum cliente consome) — vale
  só a detecção post-hoc.
- Flag desligada (default): nenhum perfil é escrito — vale só a detecção.
- `llc2` indisponível: degradação graciosa (sem perfil, sem bloqueio);
  a detecção file-based segue se `llc_replay.zones` importar.

## 5. Vocabulários best-effort (honestidade sobre os mapas)

Só o mapa `claude-code` é exato (testado contra o comportamento do cliente).
Os mapas `opencode`/`codex`/`cursor` seguem a convenção minúscula pública e
**não foram certificados** contra os clientes — estão marcados `best-effort`
no código (`_CLIENT_TOOL_ALIASES`). Para certificar um cliente: confirmar a
lista de tools e o formato do arquivo de permissões contra a documentação
oficial, atualizar o mapa e trocar o envelope `generic` pelo nativo em
`ClientPermissionProfile.write()`.

## 6. Pontos de wiring (código)

- `llc_harness/pipeline.py::step_run` — aplica perfil após `machine.start`
  (flag) + detecção post-hoc após `agent_invoke` (sempre, warn-only).
- `llc2/capabilities.py` — `generate_permission_profile(state, client)`,
  `detect_modified_file_violations(diff, machine=…)` (tool calls declarados
  como `unobserved`), `detect_capability_violations` (requer tool calls —
  só usável com observabilidade real, ex.: SDK futuro).
- Zonas: `llc_replay.zones.is_red_zone` (import tardio — evita ciclo
  `llc2 ↔ llc_replay`).

## 7. Escrita de perfis: backup, nunca clobber silencioso

Aplicar um perfil sobrescreve o arquivo de destino — inclusive
`.claude/settings.local.json` do usuário quando o cliente é claude-code
(zona config 🔴, por isso a flag default é `0`). Para não destruir
configuração alheia sem recuperação:

- Arquivo existente com conteúdo diferente é preservado em `<nome>.bak`
  (último backup) antes da escrita;
- Reescrita idêntica é no-op (sem churn, sem backup).

Não foi adotado merge (interseção/união) com o settings existente: qualquer
fusão destruiria silenciosamente uma das duas intenções (a do usuário ou a
da política de estado). Backup explícito preserva ambas recuperavelmente.

## 8. O que este documento NÃO promete

- Impedir um agente de editar zona vermelha (impossível via subprocess).
- Cobertura de tools exata para opencode/codex/cursor (best-effort, §5).
- Bloqueio em violação post-hoc (decisão consciente: warn-only).
- Atribuição perfeita pós-agente: o diff é `depois − antes` (snapshot);
  sujeira pré-existente é excluída, mas arquivo tocado antes E pelo agente
  ainda é sinalizado (fail-closed).
