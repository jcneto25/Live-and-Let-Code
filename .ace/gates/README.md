# Registros históricos de gates ACE

Este diretório é o repositório canônico para registros de gates históricos que
não são sessões ACE completas e, portanto, não devem ser colocados em
`.ace/sessions/` nem no `index.json`.

## Formato

Cada arquivo pode conter um ou mais blocos append-only `<gate_result>` com os
atributos canônicos do gate, incluindo `step`, `decision`, `decision_id`,
`policy_version`, `thresholds_hash` e `timestamp`.

Esses registros são evidência de decisões de gate, não sessões. Eles não têm
frontmatter de sessão, `session_id`, `context_seed` ou ciclo
`initialize_session.py` → `finalize_session.py`.

## Validação

O conteúdo deve manter tags balanceadas. A validação geral de sessões não deve
indexar nem exigir cobertura ACE para arquivos deste diretório. A ferramenta
específica de auditoria de gates deve ser usada quando disponível.

## Imutabilidade

Registros históricos são append-only. Não mover registros para
`.ace/sessions/` para silenciar verificações: sessões históricas são imutáveis
e só podem ser criadas pelo inicializador ACE.
