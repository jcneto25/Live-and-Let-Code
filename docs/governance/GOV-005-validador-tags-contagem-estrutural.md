# GOV-005: Contagem estrutural no validador canônico de tags

**Status**: addressed
**Data de abertura**: 2026-10-09
**Step de origem**: 11
**PRP relacionado**: PRP-ACE-TAGS / GOV-003/R1

## Sintoma

`validate-tags.py` acusava sessões balanceadas como desbalanceadas. A causa era
assimetria entre a detecção de aberturas e fechamentos:

- `_tag_opens()` tentava ignorar menções em prosa;
- `validate_balanced_tags()` contava todos os fechamentos com `re.findall()`;
- `fix_unbalanced_tags()` repetia a mesma contagem assimétrica e podia escrever
  fechamentos extras em sessões já balanceadas.

Evidências reproduzidas:

| Sessão | Tag | Aberturas filtradas | Fechamentos crus | Contagem estrutural |
|---|---|---:|---:|---:|
| `2026-08-06-017` | `action` | 9 | 8 | 8/8 |
| `2026-10-09-005` | `action` | 7 | 6 | 6/6 |
| `2026-10-09-005` | `learning_point` | 11 | 8 | 8/8 |
| `2026-10-09-005` | `context_seed` | 2 | 3 | 2/2 |

Os quatro casos eram falsos positivos; nenhum era desbalanceamento real.

## Decisão

Usar uma única contagem estrutural simétrica para validação e correção:

- remover comentários HTML antes da contagem;
- reconhecer aberturas reais no início de uma linha, preservando a heurística
  histórica para tags reais sem atributos;
- reconhecer fechamentos somente quando terminam a linha;
- usar a mesma função em `validate_balanced_tags()` e `fix_unbalanced_tags()`;
- aplicar a mesma distinção estrutural a `_tag_opens()`, para que validações de
  atributos também ignorem citações inline.

A posição na linha é necessária porque uma citação inline pode conter atributos,
ou pode compartilhar a linha com um fechamento legítimo do bloco externo.

## Validação TDD

Testes adicionados em `test_validate_tags.py` cobrem:

1. citação inline de `<action>` em uma ação real;
2. `<learning_point>` citando a própria tag;
3. citações com atributos não disparando validação de atributos;
4. `--fix` não modificando uma sessão estruturalmente balanceada.

Resultado: **20 testes passaram**. A validação histórica do hook permanece em
0/76 sessões reais; a mutação do hook detecta 156/156 fechamentos removidos.

## Registros históricos fora de `.ace/sessions/`

Arquivos como `.ace/gates/2026-10-07-007.md` são registros históricos de gate,
não sessões. Eles não devem ser recriados em `.ace/sessions/` nem adicionados ao
`index.json`, pois isso violaria a imutabilidade e o ciclo de criação ACE.

O diretório `.ace/gates/` é documentado por seu `README.md`; a validação de
sessões percorre exclusivamente `.ace/sessions/*.md` e o pre-commit não trata
arquivos de gates como sessões.

## Reparações históricas explícitas

A sessão `2026-10-09-006` foi criada antes da correção do extrator e herdou um
fragmento corrompido do seed anterior. Como sessões ACE são imutáveis, ela não
foi editada diretamente. A reparação foi feita por
`.ace/scripts/repair_session.py`, mutador explicitamente allowlisted que aceita
somente o ID 006, exige a sessão-fonte 005, cria backup, exige correspondência
única, é idempotente e recusa outros IDs.

O mesmo reparador possui uma operação independente e allowlisted para preencher
`files_touched` somente nas sessões históricas `2026-10-09-004` e
`2026-10-09-005`. Essa operação:

- extrai exclusivamente `<file_delta>` explícitos;
- ignora comentários HTML;
- deduplica preservando ordem;
- cria backup antes da escrita;
- recusa sessões fora da allowlist;
- recusa arquivos sem `file_delta` confiável.

As sessões 006 e 007 não foram preenchidas por inferência: não possuem
`file_delta` e permanecem documentadas como sessões sem cobertura de arquivo.

## Limitação conhecida

A heurística depende do formato canônico de sessões ACE: containers reais são
ancorados em linhas e fechamentos terminam linhas. Se um novo formato permitir
containers arbitrariamente inline, deverá ser introduzido um parser XML/lexer
compartilhado e novos testes antes de alterar esta regra.

## Relação com GOV-004

GOV-004 documenta a mesma classe de falso positivo no hook de pre-commit.
Este GOV registra que o validador canônico tinha uma segunda implementação
assimétrica. A prevenção adotada é manter as duas contagens estruturais
sujeitas a testes de regressão equivalentes.
