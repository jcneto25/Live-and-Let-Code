# ADR-001: Enforcement determinístico da Autoridade de Conversão via pre-commit

> **Status:** Aceito
> **Data:** 2026-07-31
> **Decidido por:** Equipe LLC
> **Última revisão:** 2026-07-31
> **Revisores:** — (auditoria autônoma da metodologia, repo da própria metodologia)
> **GOV relacionado:** GOV-001

---

## 1. Contexto

O artigo "Cheap Code, Costly Judgment" (Davis et al.) e a análise em
`docs/article-parallel-llc.md` identificam que progresso sustentável agentic vem de
converter falhas estruturais em governança durável. O LLC institucionalizou isso no
Step 11.4 (Governance Conversion), com GOVs imortais e **Autoridade de Conversão**:
qualquer operador pode registrar um GOV, mas a *instalação* de mecanismos de
governança (hooks, lints, fitness functions, gates) exige decisão rastreável.

O problema: essa regra era apenas **advisory** (texto em CONTEXT.md/AGENTS.md). Nada
impedia um agente de alterar `.ace/scripts/pre-commit.sh`, `fitness_functions/`,
`gates.json` ou `arch-config.yaml` sem qualquer vínculo com uma decisão GOV/ADR —
silenciosamente mudando as regras do jogo sem evidência da tomada de decisão.

**Fatores relevantes:**
- Mecanismos zona 🔴 são os *blocos de construção* da governança ex-ante do LLC —
  alterá-los sem rasto quebra a propriedade central da metodologia
- A solução precisa ser **tool-agnostic** (funciona para qualquer cliente de IA,
  pois roda no git, independente do agente)
- Precisa coexistir com correções de emergência (bypass legítimo existe, mas deve
  deixar evidência)
- GOV-001 já implementa a resposta; este ADR registra a decisão arquitetural formal

## 2. Decisão

Alteração de mecanismo determinístico de governança **só entra no histórico se o
mesmo commit incluir um GOV** (`docs/governance/GOV-*.md`) **ou ADR**
(`docs/architecture/adr/*.md`) que justifique a mudança.

Implementação: seção 9 de `.ace/scripts/pre-commit.sh` ("Autoridade de Conversão")
bloqueia o commit (`exit 1`) quando o diff staged toca:
- `.ace/scripts/pre-commit*.sh`, `.ace/scripts/llm-validation.sh`
- `.ace/scripts/fitness_functions/`, `.ace/scripts/fitness-functions.py`
- `.ace/config/gates.json`, `.ace/config/arch-config.yaml`
- `.pre-commit-config.yaml`

sem encontrar `docs/governance/GOV-*` ou `docs/architecture/adr/*` no mesmo stage.

Bypass emergencial: `git commit --no-verify` — a mensagem de recusa do hook fica
registrada no log do commit (auditável a posteriori).

## 3. Consequências

### Positivos
- ✅ Toda mudança em guardrail tem vínculo forçado com a deliberação que a motivou
- ✅ Tool-agnostic: o git executa o hook independente do cliente de IA
- ✅ Self-governing: o próprio mecanismo entrou em vigor já coberto por GOV-001
  (goose-and-gander — a regra cobre o commit que a instala)
- ✅ Preserva velocidade para mudanças legítimas (basta commitar GOV/ADR junto)

### Negativos / Custos
- ⚠️ Falso positivo aceito: refactors puramente cosméticos (formatação, typo em
  comentário) nesses arquivos também exigem GOV/ADR — mitigação: `--no-verify`
  documentado como saída de emergência auditável
- ⚠️ Regra é local ao repo; não protege mudanças feitas fora do fluxo git
  (ex.: edição direta em produção) — fora de escopo conhecido e aceito

### Alternativas consideradas
1. **Advisory apenas** (status quo): rejeitada — advisory falhou na prática (o
   próprio pacote GOV foi implementado alterando hooks sem GOV/ADR)
2. **Arquitetural** (tornar hooks imutáveis): rejeitada — o trabalho LLC exige
   alterar hooks; restrição deve ser de *rastreabilidade*, não *imutabilidade*
3. **Mensagem de commit com "GOV-NNN"**: rejeitada — trivialmente contornável,
   sem evidência real da decisão

## 4. Validação

- Testado em 3 cenários em 2026-07-31 (sessão 2026-07-31-001):
  hook-only → **bloqueia** ✅; hook+GOV → **passa** ✅; GOV-only → **passa** ✅
- Compromisso de auto-aplicação: o commit que instala a seção 9 passou por ela
  (carregava GOV-001 no mesmo stage)
