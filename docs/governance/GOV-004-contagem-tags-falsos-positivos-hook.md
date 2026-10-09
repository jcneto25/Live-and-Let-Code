# GOV-004: Contagem de tags do pre-commit gera falsos positivos com textos literais

**Status**: addressed
**Data de abertura**: 2026-10-09
**Data de instalação**: 2026-10-09
**Data de fechamento**: (pendente — 3 PRPs sem reincidência)
**Step de origem**: 11 (Execução)
**PRP relacionado**: (nenhum — manutenção do próprio harness)

## Sintoma

A instalação do framework `pre-commit` (2026-10-09) ativou o passo 5 do
`.ace/scripts/pre-commit.sh`, que passou a bloquear **todos** os commits com 4
erros de "tags desbalanceadas" em sessões que estão perfeitamente balanceadas:

```
❌ 2026-08-06-014.md — tags <gate_result> desbalanceadas (abre: 2, fecha: 1)
❌ 2026-08-06-017.md — tags <action_log> desbalanceadas (abre: 3, fecha: 1)
❌ 2026-08-06-018.md — tags <action> desbalanceadas (abre: 7, fecha: 6)
❌ 2026-08-06-018.md — tags <action_log> desbalanceadas (abre: 2, fecha: 1)
```

Nenhuma dessas sessões tem tag realmente desbalanceada — o verificador
inteligente `validate-tags.py` não as acusa.

## Contexto

Ativação do hook em `development` (repo "Live and Let Code") em 2026-10-09,
durante a manutenção da garantia descrita no AGENTS.md ("commit com código sem
sessão é rejeitado"). O hook nunca tinha rodado neste clone: `.git/hooks/pre-commit`
não existia e `pre-commit install` nunca havia sido executado.

## Classe de Falha

Falha Estrutural — a camada determinística de validação existia, mas com um
verificador duplicado e mais fraco do que o verificador da camada advisory
(`validate-tags.py`).

## Impacto

Alto — o mecanismo determinístico rejeitava commits legítimos. Um gate que
bloqueia o trabalho correto é pior que ausente: induz ao `--no-verify`
contornando **toda** a validação, inclusive a parte que funciona.

## Evidência

Contagem no arquivo original vs. no corpo da tag (2026-10-09):

| Sessão | Tag | Linha citada | Texto literal contado como abertura |
|---|---|---|---|
| `2026-08-06-014` | `<gate_result>` | 35 | `<description>… leitura de <gate_result> real (RF-G1B.1-7)` |
| `2026-08-06-017` | `<action_log>` | 40 | `<description>Bug latente do harness: <action_log> casava no regex…` |
| `2026-08-06-017` | `<action_log>` | 69 | `<context_seed>… <action_log> casava no regex de <action> …` |
| `2026-08-06-018` | `<action>` | 18 | `<context_seed>… regex de <action> e engolia o 1º action real …` |
| `2026-08-06-018` | `<action_log>` | 18 | idem |

- Contagem por ocorrência **após** remover os corpos, em `2026-08-06-017`:
  8 `<action` reais (linhas 35-42) e 8 `</action>` — **balanceado**. O arquivo
  nunca esteve desbalanceado.
- **O `validate-tags.py` cai na mesma armadilha.** Sua rodada sem `--fix` reportou
  `2026-08-06-017` `<action>` 9/8, contando a citação literal `<action>` dentro do
  `<description>` da linha 40 como se fosse uma abertura. O `--fix`, executado
  nesta manutenção com autorização explícita, **anexou um `</action>` espúrio** ao
  fim do arquivo — transformou um arquivo balanceado (8/8) em desbalanceado (8/9).
  Revertido com `git checkout -- .ace/sessions/2026-08-06-017.md` no mesmo dia.
  A falha é de **contagem**, não do hook: atinge também o verificador "inteligente".
- Segunda instância da mesma classe nesta manutenção: o passo 5 do hook foi
  corrigido com `sed` range (`/<description>/,/<\/description>/d`), que só testa o
  fim a partir da linha seguinte — apagava do primeiro `<description>` até o EOF e
  elevou os 5 erros para 24. Substituído por `re.sub(..., flags=re.S)`.
- Ironia registrada: `2026-08-06-017` e `2026-08-06-018` são as sessões que
  documentaram a correção de **exatamente essa classe de bug** em
  `finalize_session/extract.py` (`_strip_comments`, "seed com tags literais",
  "placeholders em comentários").

## Causa Estrutural

O passo 5 usava `grep -cE "<$tag\b"` sobre o arquivo **inteiro**, sem distinguir
ocorrência real de tag de citação textual dentro de `<description>` ou
`<context_seed>`. O passo 5 duplicava uma checagem que `validate-tags.py` já faz
de forma correta (ciente de conteúdo), mas o hook não o invocava para esse fim —
chamava apenas `validate-tags.py --coverage`.

O `grep -c` também conta **linhas**, não ocorrências, mascarando outros casos.

## Decisão

Resposta de Controle Determinístico: o passo 5 passa a contar sobre uma cópia do
arquivo com os corpos de `<description>`, `<file_delta>`, `<result>` e
`<context_seed>` removidos — são os corpos que podem citar tags literalmente.
`<context_seed>` é contado no arquivo **original**, porque é o próprio balanceamento
dele que precisa ser aferido.

Não foi escolhida alternativa de escapar os textos literais nas sessões
(`&lt;gate_result&gt;`): isso reescreveria registro histórico de sessões fechadas
para agradar um contador, invertendo a relação entre dado e verificação.
Tampouco foi escolhido delegar o passo 5 ao `validate-tags.py` completo, porque
ele valida 62 outras regras (campos `<dependencies>`, atributos de `<action>`)
que o hook deliberadamente não bloqueia — trocar de 4 erros por 62 seria regressão.

## Mecanismo Instalado

`.ace/scripts/pre-commit.sh`, passo 5 (implementado em **Python**, `re.sub` com
`flags=re.S` — **não** em `sed`):
- Remove os corpos citantes antes de contar: `<description>`, `<file_delta>`,
  `<result>`, `<context_seed>`, `<learning_point>`, `<thinking>`
- Conta `<context_seed>` sobre o arquivo original (só os *outros* corpos citam
  tags)
- Comentário no código remetendo a este GOV

> **Correção (2026-10-09, sessão `2026-10-09-005`):** a redação anterior desta
> seção dizia "remove corpos com `sed`". Era falsa em dois níveis: o código usa
> `re.sub` (o `sed` foi justamente a tentativa que falhou — ver "Segunda
> instância" acima), e a lista de corpos estava incompleta (faltavam
> `<learning_point>` e `<thinking>`, causa da 3ª instância — ver abaixo).

## Terceira Instância (2026-10-09, sessão `2026-10-09-004`)

A 1ª correção deste GOV cobriu `<description>`, `<file_delta>`, `<result>` e
`<context_seed>`, mas o defeito **reapareceu na própria sessão que o corrigia**:
`2026-10-09-004.md` foi acusada de `<action>` 11/10 porque o corpo do seu
`<learning_point>` cita literalmente `` `<action>` ``.

| Correção | Corpos removidos antes de contar | Erros restantes |
|---|---|---|
| 1ª (2026-10-09-004) | description, file_delta, result, context_seed | 1 |
| **2ª (2026-10-09-005)** | **+ learning_point, thinking** | **0** |

Validado sobre as 76 sessões: com a 1ª lista, 1 arquivo acusa falso positivo;
com a 2ª, nenhum.

## Quarta Instância — a armadilha da ORDEM (2026-10-09, sessão `2026-10-09-005`)

Com a 2ª lista, o hook passou a acusar **a própria sessão `2026-10-09-005`**:

```
❌ 2026-10-09-005.md — tags <learning_point> desbalanceadas (abre: 1, fecha: 0)
❌ 2026-10-09-005.md — tags <context_seed> desbalanceadas (abre: 3, fecha: 2)
```

O arquivo está perfeitamente balanceado. A causa **não** era uma lista
incompleta, e sim a **ordem das remoções**: um `<learning_point>` citava
`<context_seed>`. Como o strip de `context_seed` rodava junto dos demais, o
casamento não-guloso

```
<learning_point ...> ... </context_seed>
```

fechava no `</context_seed>` **citado** e engolia o `</learning_point>` real —
que então aparecia como 1 abertura sem fechamento.

**Correção:** `context_seed` é removido **por último**, em passada separada
(`NO_CONTEXT_SEED_BODIES` + `ALL_BODIES`). Assim nenhum strip de corpo externo
pode consumir o fechamento de um `<learning_point>`.

Validado em 6 casos sintéticos: detecta `<action>`, `<context_seed>` e
`<learning_point>` sem fechamento; silencia citação literal de `<action>`,
`<action_log>` e `<context_seed>`. E 0 erros nas 76 sessões reais.

> **Lição (3 correções, 3 instâncias):** enumerar "casos conhecidos" reproduz o
> bug no caso seguinte. A validação tem de rodar contra **todas** as sessões, e
> a ordem das operações de strip é parte do algoritmo — não detalhe.

## Quinta Instância — o strip não resolve (2026-10-09, sessão `2026-10-09-005`)

Corrigida a ordem, o hook voltou a acusar **a própria sessão que documentava o
bug** (5ª instância, e desta vez **não sintética**):

```
❌ 2026-10-09-005.md - tags <learning_point> desbalanceadas (abre: 0, fecha: 1)
```

A sessão descrevia o defeito em prosa — "o strip engolia o
`</learning_point>` real" — citando o **fechamento** dentro de um
`<learning_point>`. O strip não-guloso `^<learning_point>.*?</learning_point>$`
fechou no fechamento **citado**, e o fechamento **real** ficou órfão.

**Isto é insanável por remoção de corpo.** Um strip não distingue o fechamento
real do citado quando ambos estão no mesmo corpo; qualquer lista de corpos
apenas desloca o problema para o corpo seguinte. A classe de falha é a
**contagem**, não a lista.

### Solução adotada: contagem estrutural

Conta-se apenas tag **estrutural**, definida por posição na linha:

| | Padrão | Exemplo que conta |
|---|---|---|
| Abertura | `^[ \t]*<tag(?=[\s>/])` | `<action type="file_modify">` no início da linha |
| Fechamento | `</tag>[ \t]*$` | `</learning_point>` no fim da linha |

Citação em prosa fica no **meio** da linha e não conta. Comentários HTML são
removidos antes (carregam os placeholders do template).

`re` com `flags=re.M` — **sem** range de `sed`.

### Validação

| Verificação | Resultado |
|---|---|
| 76 sessões reais | **0 erros** (a versão por strip acusava 1) |
| 7 casos sintéticos | **7/7** — detecta `<action>`/`<context_seed>`/`<learning_point>` sem fechar; silencia citação de `<action>`, de `</learning_point>` e de comentário HTML |
| Mutação (remover 1 fechamento estrutural em cada sessão) | **156/156** detectados — mesmo índice da versão por strip, **sem** o falso positivo |
| Falso negativo introduzido | nenhum |

> A versão por strip tinha sensibilidade 156/156 e **1 falso positivo**. A
> estrutural tem 156/156 e **0**. É estritamente superior neste corpus.

## Histórico de Correções (5 tentativas)

| # | Tentativa | Resultado |
|---|---|---|
| 0 | `grep -cE "<$tag\b"` no arquivo inteiro | 4 falsos positivos (014/017/018) |
| 1 | `sed` range `/<tag>/,/<\/tag>/d` | apagou até o EOF — 5 erros → **24** |
| 2 | Python `re.sub`, 4 corpos | 1 falso positivo (`2026-10-09-004`) |
| 3 | + `learning_point`, `thinking` (6 corpos) | 1 falso positivo por **ordem** (`2026-10-09-005`) |
| 4 | `context_seed` em passada separada | 1 falso positivo por citação do **próprio fechamento** |
| **5** | **contagem estrutural (posição na linha)** | **0 falsos positivos, 156/156 na mutação** |

## Dívida Aberta

`validate-tags.py` **não** foi corrigido: segue contando a citação literal dentro
de `<description>` e reporta `2026-08-06-017` `<action>` 9/8 (falso positivo — o
arquivo está 8/8). E `--fix` continua perigoso nesse caso: anexa `</tag>` a um
arquivo já balanceado. Enquanto isso não for tratado, `--fix` **não** deve ser
executado sobre sessões históricas sem inspeção prévia.

## Área Afetada

`.ace/scripts/pre-commit.sh` (mecanismo zona 🔴 — este documento é a
rastreabilidade exigida pelo passo 9, criado no mesmo commit).

## Validação Posterior

- `bash .ace/scripts/pre-commit.sh` → exit 0 com todas as sessões íntegras
- Regressão conhecida: reintroduzir a contagem sem remover os corpos citantes
  volta a reportar os mesmos falsos positivos nas mesmas sessões (4 em
  014/017/018 com a 1ª lista; 1 em `2026-10-09-004` se `<learning_point>` não
  estiver na lista)
- `git log --oneline -- .ace/scripts/pre-commit.sh` deve citar este GOV no mesmo
  commit de cada alteração futura

## Status da Reincidência

0/3 PRPs sem reincidência desde a instalação (2026-10-09)
