# GOV-001: Mecanismos zona 🔴 alteráveis sem rastreabilidade de decisão

**Status**: addressed
**Data de abertura**: 2026-07-31
**Data de instalação**: 2026-07-31
**Data de fechamento**: (pendente — 3 PRPs sem reincidência)
**Step de origem**: 11.4 (auditoria de conformidade da própria metodologia)
**PRP relacionado**: PRP-GOV-004

## Sintoma

Commits que alteram mecanismos determinísticos de governança (pre-commit hooks,
fitness functions, `gates.json`, `arch-config.yaml`) podiam ser feitos sem nenhum
artefato que registrasse a decisão — quebra da **Autoridade de Conversão** definida
em `CONTEXT.md`: quem modifica o ambiente de engenharia sem deixar rastro da decisão
inválida o ciclo `execução → falha estrutural → conversão em governança`.

## Contexto

Detectado durante auditoria do pacote GOV (31/07/2026): a implementação do Step 11.4
introduziu 2 scripts novos e alterou `initialize_session`, `gates.json` foi alterado
manualmente depois, e **nenhum** desses commits citou GOV/ADR. A metodologia tinha
a regra *documentada* mas nenhum *enforcement* — falha clássica de
"advisory onde deveria ser determinístico" (criticada no `article-parallel-llc.md` §Convergências).

## Classe de Falha

Falha Estrutural — ambiente de engenharia sem salvaguarda (camada determinística da
Autoridade de Conversão ausente).

## Impacto

Alto — permite que controles determinísticos sejam alterados silenciosamente,
subtraindo da metodologia a propriedade que ela mais defende (governança explícita
sobre o que restringe o agente).

## Evidência

- `git log` pré-31/07: nenhum commit de `.ace/scripts/*hook*`, `fitness_*`,
  `gates.json` referencia GOV ou ADR
- `docs/governance/` não existia até 2026-07-30 — mecanismos alteráveis "em silêncio"

## Causa Estrutural

O pre-commit hook já validava integridade ACE (sessões, seeds, tags) mas **não**
cruzava diff staged com a fronteira "mecanismo determinístico". A fronteira era
apenas declarativa (zona 🔴 em AGENTS.md), sem verificação.

## Decisão

Resposta de Controle Determinístico: seção 9 no `pre-commit.sh` — diff staged em
mecanismo zona 🔴 **exige GOV ou ADR no mesmo commit**; o bypass (`--no-verify`)
permanece disponível para emergências, com a recusa impressa no log (auditável).

Não foi escolhida resposta arquitetural (ex.: tornar os hooks imutáveis) porque
a natureza do trabalho LLC exige poder alterá-los — a restrição correta é de
*rastreabilidade*, não de *imutabilidade*.

## Mecanismo Instalado

Seção 9 do `.ace/scripts/pre-commit.sh`:
- Padrão de caminhos monitorados: `pre-commit*.sh`, `llm-validation.sh`,
  `fitness_functions/`, `fitness-functions.py`, `.ace/config/gates.json`,
  `.ace/config/arch-config.yaml`, `.pre-commit-config.yaml`
- Se diff staged toca algum → exige `docs/governance/GOV-*.md` ou
  `docs/architecture/adr/*` no mesmo commit
- Violação bloqueia o commit (`exit 1` via `ERRORS`)

## Área Afetada

.ace/scripts/pre-commit.sh, .ace/config/gates.json, docs/governance/

## Validação Posterior

- Todo commit futuro listado em `git log --oneline -- .ace/scripts/pre-commit.sh
  .ace/scripts/llm-validation.sh .ace/scripts/fitness_functions/ .ace/config/gates.json`
  deve ter GOV/ADR referenciável na árvore do commit
- Em caso de bypass, `git log --grep="no-verify"` deve permanecer vazio ou com
  justificativa em `§11` de algum PRP

## Status da Reincidência

0/3 PRPs sem reincidência desde a instalação (2026-07-31)
