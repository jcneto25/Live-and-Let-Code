# ADR-0008: Correção da Contagem de Tags XML no pre-commit.sh (bugfix zona 🔴)

> **Status:** Aceito
> **Data:** 2026-08-06
> **Decidido por:** Equipe LLC (jcneto)
> **Última revisão:** 2026-08-06
> **Revisores:** Equipe LLC

---

## 1. Contexto

O `pre-commit.sh` (zona 🔴 — mecanismo de enforcement ACE) valida o balanceamento
das tags XML nas sessões do `.ace/sessions/`. A checagem usava:

```bash
open_count=$(grep -c "<$tag" "$session_file" 2>/dev/null || echo 0)
```

O `grep` ingênuo `<action` casa **também** `<action_log>` (o wrapper de seção do
template de sessão, que abre em `<action_log>` e fecha em `</action_log>`), pois
não há âncora de palavra. Resultado: toda sessão que usa o template (que contém
o wrapper vazio `<action_log>`) era reportada com `<action>` desbalanceada.

**Fatores relevantes:**
- O template `.ace/templates/session.template.md` gera `<action_log>`/`</action_log>`
  como estrutura fixa.
- `validate-tags.py` (fonte sancionada de verdade) usa `_tag_opens` com âncora
  `\b` e critério de "tag real" (atributos, fecha na mesma linha, ou sozinha na
  linha) — **correto**. O pre-commit duplicava a checagem com lógica distinta.
- Sessões legítimas que mencionam `<gate_result>` em prosa (ex.: descrição de um
  `_gate_decision_from_session`) também eram contadas como tag aberta sem
  fechamento.
- Hooks não instalados em `.git/hooks/` — o pre-commit nunca rodava de fato;
  o bug ficava latente até o primeiro stage do `pre-commit.sh`.

---

## 2. Decisão

Alinhar a contagem do `pre-commit.sh` ao `validate-tags.py`:

```bash
open_count=$(grep -cE "<$tag\b" "$session_file" 2>/dev/null || true)
close_count=$(grep -c "</$tag>" "$session_file" 2>/dev/null || true)
```

- Âncora `\b` (word boundary): `<action\b` casa `<action ` e `<action>` mas **não**
  `<action_log>` (o `_` é word char, quebra o boundary).
- `|| true` em vez de `|| echo 0`: `grep -c` retorna exit 1 quando o count é 0,
  e o `|| echo 0` concatenava um segundo valor ao output — o `|| true` preserva
  o count real.
- Menções de tags em prosa (ex.: `<gate_result>` dentro de `<description>`) são
  escritas **sem** a forma literal de abertura quando descrevem código, para não
  serem contadas pelo `grep` (mesmo critério do `validate-tags.py`).

---

## 3. Consequências

**Positivas:**
- Pre-commit e `validate-tags.py` concordam sobre o balanceamento de tags.
- Sessões do template com `<action_log>` vazio não geram falso negativo.
- Falso positivo de "secret" em `pre-commit.sh` (patterns de URI com credenciais,
  linhas 149-151) é pré-existente e fica **fora** do escopo desta correção — o
  script só aparece no diff quando alterado; a exceção de exclusão não foi
  adicionada (bug de normalização de ponto no `SECRET_EXCLUDE`) e será tratada
  em dívida técnica separada se o script for alterado de novo.

**Negativas:**
- `pre-commit.sh` é zona 🔴: esta alteração é sancionada por este ADR-0008
  (Goose-and-Gander — a própria decisão documenta a alteração do mecanismo,
  seguindo o precedente GOV-001/commit 879a4c4).

---

## 4. Decisão Relacionada

- ADR-0001 / GOV-001 §9 — Autoridade de Conversão (zona 🔴 exige GOV/ADR).
- PRP-ACE-TAGS / GOV-003 R1 — tags ACE e validação.
