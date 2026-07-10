# Workflow Logic Audit — Live and Let Code (LLC)

**Auditor:** Senior Developer (simulação manual + execução real dos scripts)
**Branch:** `refactoring`
**Data:** 2026-07-10
**Escopo:** Verificação da lógica do workflow LLC — simulação de fluxos greenfield e brownfield, confronto entre templates × scripts × gates.json × REGISTRY, com objetivo de afastar riscos de erro semântico ou lógico.
**Suíte de testes no momento da auditoria:** 67 passed (mas ver F-01 — os testes não cobrem os caminhos de runtime afetados).

---

## 1. Sumário Executivo

A auditoria identificou **2 defeitos CRITICAL** que bloqueiam a execução real do workflow em runtime, **3 HIGH** que silenciosamente neutralizam gates/checks semanticamente obrigatórios, **4 MEDIUM** com impacto em UX/consistência e **5 LOW** cosméticos/de-documentação.

| ID  | Sev       | Componente                      | Resumo                                                                 | Runtime? |
|-----|-----------|---------------------------------|------------------------------------------------------------------------|----------|
| F-01 | CRITICAL | `llc_harness/common.py`         | Path regression: `ACE_DIR`/`SCRIPTS_DIR`/`GATES_FILE` apontam para `.ace/scripts/scripts/...` (off-by-one do refactor de pacote). Quebra session init + descarrega gates.json. | Sim |
| F-02 | CRITICAL | `llc/gates_meta.py` + `llc_harness/gates.py` | `llc gate run --gate security/null-safety/owasp` crasha com `UnknownStepError`. 3 de 5 aliases de gate produzem gate-keys que `normalize_step` não resolve. | Sim |
| F-03 | HIGH     | `llc_steps/registry.py`         | Gates delta Δ.0/Δ.1 definidos em gates.json mas REGISTRY step 0.2/0.3 têm `gate=None` → `_run_delta_analysis` auto-aprova sem mostrar checklist. | Semântico |
| F-04 | HIGH     | `llc_delta/report.py`           | Parser do DELTA_REPORT busca strings sem acento ("Alteracao","Necessarios","Classificacao","Iteracao proposta") mas o template usa acentos ("Alteração","Necessários","Classificação","Iteração proposta") → `affected_prps`/`new_prps`/`change_type`/`iteration` sempre vazios. | Semântico |
| F-05 | MEDIUM   | `llc_delta/report.py`           | Parser da tabela "Steps a Pular" captura a linha de cabeçalho como skip entry (sem filtro de header como há em execute_steps). | Semântico |
| F-06 | MEDIUM   | `llc/cli.py`                    | Definição duplicada de `gate`: `@cli.command() def gate(step)` (L239) sombreado por `@cli.group() def gate()` (L279). `llc gate --step N` é dead code. | Sim |
| F-07 | MEDIUM   | `llc/gates_meta.py` + `normalize.py` | `_get_gate_id` faz lowercase; `normalize_step` é case-sensitive → `"Security"`/`"SECURITY"` não resolvem. Inconsistência de case. | Semântico |
| F-08 | MEDIUM   | `llc_steps/registry.py`         | Skill órfã `llc-step-0-greenfield.md`: step "0" tem `skill_file=None` → `llc run --step 0` falha em skill_load. | Sim |
| F-09 | MEDIUM   | `llc_harness/skill.py`          | `AGENTS.md` não existe no repo root (só `docs/templates/AGENTS_TEMPLATE.md`) → `load_agents_conventions()` retorna "" silenciosamente; agentes não recebem Document Index/zonas vermelhas. | Semântico |
| F-10 | LOW      | `DELTA_REPORT_TEMPLATE.md`      | Template refere gate "10-COVERAGE" (L134) mas gates.json key é "10.8"; alias existe em GATE_ALIASES mas não em gates.json. | Doc |
| F-11 | LOW      | `llc/cli.py`                    | Mensagem quickstart diz "Gates incluídos: 1, 4, 11" mas `--quickstart` roda todos os 16 steps 0.5→11 (incl. security/null/coverage). | Doc |
| F-12 | LOW      | `llc_wave/run.py`               | Help text diz "cd .ace/scripts && python llc.py" mas paths cwd-relativos (`docs/skills`, `.ace/index.json`) exigem repo root. | Doc |
| F-13 | LOW      | `prp_verify/coverage.py`        | Geração de cobertura é JS-only (vitest/jest); projetos Python/Go recebem WARN, mas o timeout de 120s×2 em `npx` é desperdício para stacks não-JS. | Semântico |
| F-14 | LOW      | `llc_steps/registry.py` (D-02)  | Sub-skills 5a/5b/5c/11a/11b/8b existem mas não estão cabeadas no REGISTRY; `llc-step-11.md` as cita como pré-requisitos obrigatórios. | Semântico |

**Conclusão:** O workflow **não executa corretamente em runtime** hoje (F-01 + F-02). Os 67 testes passam porque caracterizam lógica em isolamento com paths mockados, sem exercitar os caminhos subprocess/arquivo reais. Recomenda-se corrigir F-01/F-02 antes de qualquer outra ação.

---

## 2. Metodologia

1. **Mapeamento completo:** leitura de `gates.json`, `llc_steps/registry.py` (REGISTRY), `llc_steps/models.py`, `llc_steps/normalize.py`, todos os submódulos de `llc_harness/`, `llc_delta/`, `llc_wave/`, `llc/`, `prp_verify/`, `finalize_session/`, `initialize_session/`.
2. **Inventário de skills:** 42 arquivos em `docs/skills/` cruzados com `skill_file` do REGISTRY (orfanato detectado).
3. **Inventário de templates:** `PRP_TEMPLATE.md`, `DELTA_REPORT_TEMPLATE.md`, `EXECUTION_WAVES_TEMPLATE.md`, `session.template.md`, templates de security/testing/planning.
4. **Simulação greenfield:** trace manual de `llc pipeline --from 0.5 --to 11.1` (17 steps in_pipeline) verificando session_start → skill_load → agent_invoke → gate_check → session_end em cada step.
5. **Simulação brownfield:** trace de `llc delta start --iteration v2` → `llc pipeline --delta` verificando `_run_delta_analysis`, `parse_delta_report`, `is_step_skipped` (ALWAYS_RUN), skip notes.
6. **Execução real:** comandos `llc` invocados para confirmar crashes e paths (não só análise estática).
7. **Cross-check matricial:** gates.json × REGISTRY × GATE_ALIASES × templates.

---

## 3. Simulação Greenfield

### 3.1 Fluxo esperado: `llc pipeline` (default 0.5 → 11.1)

Sequência `pipeline_steps('0.5','11.1')` = 17 steps:
`0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 10.6, 10.7, 10.8, 11, 11.1`

Excluídos (`in_pipeline=False`): `0, 0.1, 0.2, 0.3, 11.2, 11.3`.

### 3.2 Trace por step (estado real constatado)

| Step | Gate | Skill file | Resultado real | Bloqueio |
|------|------|------------|----------------|----------|
| 0.5  | 1    | llc-step-0-5 | session_start CRASHA (F-01: SCRIPTS_DIR/initialize_session.py não encontrado) | F-01 |
| 1    | 2    | llc-step-1   | idem | F-01 |
| 2-10 | 3-11 | llc-step-N   | idem — todo `pipeline_run` aborta no primeiro `step_run` | F-01 |
| 10.6 | 11-SEC | llc-step-11-security | mesmo se F-01 corrigido: gate_check mostra checklist VAZIO (gates.json não carregado → F-01) | F-01 |
| 10.7 | 12-NULL | llc-step-12-null-safety | idem | F-01 |
| 10.8 | 10.8 | llc-step-10-8-test-coverage | idem | F-01 |
| 11   | None (QA) | llc-step-11 | idem; após F-01, session_end dispara `_maybe_block_on_prp_verify` (step 11) | F-01 |
| 11.1 | 11-OWASP | llc-step-11-owasp-security | idem | F-01 |

**Gate check (pós-F-01):** mesmo após corrigir paths, `gate_check(spec.id)` chama `get_gate_checklist` → `load_gates_config()` → `GATES_FILE.exists()` retorna False (path quebrado) → fallback `{"gates": {}}` → **todos os checklists vazios**. O gate mostra apenas `[A]provar [R]ejeitar` sem critérios. Isso neutraliza silenciosamente todo o sistema de gates.

### 3.3 Quickstart (`--quickstart`)

Define `to_step="11"`. `pipeline_steps('0.5','11')` = 16 steps (exclui 11.1/11.2/11.3). Mensagem diz "Gates incluídos: 1, 4, 11" mas na realidade roda 16 steps (F-11).

### 3.4 Step 0 (Ingestão) / 0.1 (Docling)

Fora do pipeline (`in_pipeline=False`). `llc run --step 0` falha em `skill_load` pois `skill_file=None` (F-08), embora `docs/skills/llc-step-0-greenfield.md` exista (órfã).

---

## 4. Simulação Brownfield

### 4.1 Fluxo esperado: `llc delta start --iteration v2` → `llc pipeline --delta`

1. `delta_start` verifica `docs/business/ingestion/converted/` tem documentos.
2. Se `DELTA_REPORT.md` não existe → `_run_delta_analysis`:
   - Step Δ.0 (0.2): `session_start("0.2")` → `gate_check("0.2")` → `session_end`.
   - Step Δ.1 (0.3): idem.
3. `pipeline --delta`: lê `DELTA_REPORT.md`, loop com smart skip.

### 4.2 Resultado real constatado

| Fase | Esperado | Real | Bloqueio |
|------|----------|------|----------|
| `session_start("0.2")` | inicializa sessão | CRASH (F-01: SCRIPTS_DIR quebrado) | F-01 |
| `gate_check("0.2")` (Gate Δ.0) | mostra checklist Δ.0 de gates.json | `gate=None` no REGISTRY → auto-aprova sem checklist | F-03 |
| `gate_check("0.3")` (Gate Δ.1) | mostra checklist Δ.1 de gates.json | idem — `gate=None` | F-03 |
| `parse_delta_report()` | extrai change_type, iteration, affected_prps, new_prps, skip_steps | `change_type=unknown`, `iteration=None`, `affected_prps=[]`, `new_prps=[]` (acentos não casam) | F-04 |
| `skip_steps` parsing | lista de {step_id, reason} | inclui linha de cabeçalho "Step\|Justificativa\|..." como skip entry | F-05 |
| `is_step_skipped` (ALWAYS_RUN) | protege 10,10.6,10.7,10.8,11,11.1,11.2 | lógica correta — Always-run nunca é pulado | OK |

### 4.3 Efeito do F-04 no brownfield

Com o template `DELTA_REPORT_TEMPLATE.md` (acentuado: "Alteração", "Necessários", "Classificação", "Iteração proposta"), o parser `parse_delta_report`:
- regex `Classificacao\s*\|\s*`(\w+)`` → não casa "Classificação" → `change_type="unknown"`.
- regex `Iteracao proposta\s*\|\s*`(v[\d.]+)`` → não casa "Iteração proposta" → `iteration=None`.
- substring `"PRPs Existentes com Alteracao (PRP-A)"` ≠ `"PRPs Existentes com Alteração (PRP-A)"` → `affected_prps=[]`.
- substring `"Novos PRPs Necessarios (PRP-N)"` ≠ `"Novos PRPs Necessários (PRP-N)"` → `new_prps=[]`.

Resultado: `llc delta plan` exibe plano vazio de PRPs afetados/novos. O pipeline ainda executa (usa `skip_steps` para smart-skip), mas a rastreabilidade brownfield de PRP-A/PRP-N é perdida.

---

## 5. Achados Detalhados

### F-01 — CRITICAL: Path regression em `llc_harness/common.py`

**Localização:** `.ace/scripts/llc_harness/common.py:7-12`

```python
ACE_DIR = Path(__file__).resolve().parent.parent        # OFF-BY-ONE
SCRIPTS_DIR = ACE_DIR / "scripts"                       # → .ace/scripts/scripts (inexistente)
CONFIG_DIR = ACE_DIR / "config"                         # → .ace/scripts/config (inexistente)
GATES_FILE = CONFIG_DIR / "gates.json"                  # → .ace/scripts/config/gates.json (inexistente)
```

**Causa-raiz:** O `llc_harness.py` original era um arquivo único em `.ace/scripts/llc_harness.py`, onde `.parent.parent` = `.ace` (correto). Após o refactor para pacote `.ace/scripts/llc_harness/common.py`, o arquivo ficou **um nível mais profundo**, então `.parent.parent` agora = `.ace/scripts` (não `.ace`). O contador `.parent` não foi ajustado.

**Reprodução:**
```
$ python3 llc.py run --step 5 --task "test"
❌ Erro ao inicializar sessao:
can't open file '/home/.../.ace/scripts/scripts/initialize_session.py': [Errno 2] No such file or directory
```
```
$ python3 -c "from llc_harness.common import SCRIPTS_DIR, GATES_FILE; print(SCRIPTS_DIR.exists(), GATES_FILE.exists())"
False False
```

**Impacto (3 em 1):**
1. `session_start` invoca `SCRIPTS_DIR/"initialize_session.py"` → path inexistente → **todo `llc run`/`pipeline`/`session start`/`wave run` aborta**.
2. `session_end` invoca `SCRIPTS_DIR/"finalize_session.py"` → idem.
3. `load_gates_config()` → `GATES_FILE.exists()`=False → fallback `{"gates": {}}` → **todos os gate checklists vazios** (gates.json descarregado silenciosamente).

**Por que os 67 testes passam:** Os testes mockam `SESSIONS_DIR`, `PRE_WAVE_CHECK_SCRIPT`, etc. via `monkeypatch`, e nenhum exercita `SCRIPTS_DIR` real ou `load_gates_config` contra o arquivo físico. Há uma **lacuna de teste** nos caminhos de runtime.

**Correção proposta:**
```python
# common.py — fix off-by-one
SCRIPTS_DIR = Path(__file__).resolve().parent.parent   # .ace/scripts (2 parents: llc_harness/ → common.py)
ACE_DIR = SCRIPTS_DIR.parent                            # .ace
CONFIG_DIR = ACE_DIR / "config"
GATES_FILE = CONFIG_DIR / "gates.json"
```
Adicionar um teste characterization que asserte `SCRIPTS_DIR.exists()` e `load_gates_config()["gates"]` não-vazio.

---

### F-02 — CRITICAL: `llc gate run --gate security/null-safety/owasp` crasha

**Localização:** `.ace/scripts/llc/gates_meta.py:7-14` (GATE_ALIASES) + `.ace/scripts/llc_harness/gates.py:11` (get_gate_checklist)

**GATE_ALIASES** mapeia aliases para **gate-keys do gates.json**:
```python
GATE_ALIASES = {
    "security": "11-SEC",      # gate-key (não é step id/alias)
    "null-safety": "12-NULL",  # gate-key
    "owasp": "11-OWASP",       # gate-key
    "verify": "11.2",          # step id (funciona)
    "test-coverage": "10.8",   # step id (funciona)
    "10-coverage": "10.8",     # step id (funciona)
}
```

`gate_run` faz `gate_id = _get_gate_id(gate)` → `gate_check(gate_id)`. Mas `gate_check` → `get_gate_checklist` → `normalize_step(step)` que **só resolve step ids/aliases, não gate-keys**. `"11-SEC"` não está no REGISTRY nem no `_ALIAS_MAP` (o alias é `"11-sec"` minúsculo).

**Reprodução:**
```
$ python3 llc.py gate run --gate security
🔍 Validando Gate 11-SEC
Traceback (most recent call last):
  ...
  File ".../llc_harness/gates.py", line 11, in get_gate_checklist
    spec = normalize_step(step)
  File ".../llc_steps/normalize.py", line 33, in normalize_step
    raise UnknownStepError(f"Step desconhecido: {raw!r}")
llc_steps.models.UnknownStepError: Step desconhecido: '11-SEC'
```
Idem para `null-safety` (`12-NULL`) e `owasp` (`11-OWASP`). `verify` e `test-coverage` funcionam (mapeiam para step ids).

**Impacto:** 3 de 5 gates nomeados (Security, Null Safety, OWASP) — exatamente os gates de segurança mais críticos — são inválidos via CLI `gate run`. O caminho `pipeline`/`run` não afetado (usa `spec.id` = step id). Dry-run funciona (usa `_show_gate_checklist` com GATE_CHECKLIST hardcoded, não `gate_check`).

**Correção proposta:** Adicionar fallback de gate-key em `get_gate_checklist`:
```python
def get_gate_checklist(step):
    try:
        spec = normalize_step(step)
        gate_key = spec.gate
    except UnknownStepError:
        gate_key = step  # assume que já é uma gate-key de gates.json
    if gate_key is None:
        return None, []
    config = load_gates_config()
    gate = config.get("gates", {}).get(gate_key, {})
    return gate_key, gate.get("checklist", [])
```
Assim GATE_ALIASES pode manter gate-keys e `gate_check("11-SEC")` resolve via fallback direto em gates.json.

---

### F-03 — HIGH: Gates delta Δ.0/Δ.1 definidos mas nunca enforceados

**Localização:** `.ace/scripts/llc_steps/registry.py:8-25` (steps 0.2/0.3 com `gate=None`) vs `.ace/config/gates.json:158-177` (gates "Δ.0"/"Δ.1" com step 0.2/0.3)

**gates.json** define:
```json
"Δ.0": { "step": 0.2, "label": "Delta Impact Analysis", "checklist": [5 itens] },
"Δ.1": { "step": 0.3, "label": "Delta Grill Me", "checklist": [3 itens] }
```
Mas **REGISTRY** registra steps 0.2/0.3 com `gate=None`:
```python
"0.2": _spec("0.2", "Delta Impact Analysis", "llc-step-delta-impact", None, False, False),
"0.3": _spec("0.3", "Delta Grill Me", "llc-step-delta-grill", None, False, False),
```

`_run_delta_analysis` (pipeline.py:38-51) chama `gate_check("0.2")` e `gate_check("0.3")`, cujos comentários dizem "Gate Δ.0 — validacao humana" e "Gate Δ.1 — validacao humana". Mas `get_gate_checklist("0.2")` → `normalize_step("0.2").gate = None` → retorna `(None, [])` → `gate_check` imprime "Nenhum gate definido para step 0.2. Avancando automaticamente." e retorna `"approved"`.

**Impacto:** Os gates de validação humana do fluxo delta (Δ.0 aprova o relatório de impacto; Δ.1 aprova as respostas do grill) **nunca exigem revisão humana**. O brownfield pula a validação explícita que o template `DELTA_REPORT_TEMPLATE.md` §7 e os comentários do código assumem.

**Correção proposta:** No REGISTRY, wire gates delta:
```python
"0.2": _spec("0.2", "Delta Impact Analysis", "llc-step-delta-impact", "Δ.0", False, False, ...),
"0.3": _spec("0.3", "Delta Grill Me", "llc-step-delta-grill", "Δ.1", False, False, ...),
```

---

### F-04 — HIGH: Parser DELTA_REPORT não casa acentos do template

**Localização:** `.ace/scripts/llc_delta/report.py:40-107`

O parser busca strings **sem acento**, mas `DELTA_REPORT_TEMPLATE.md` usa **acentos portugueses**:

| Parser (report.py)                          | Template (DELTA_REPORT_TEMPLATE.md)         | Campo afetado      |
|---------------------------------------------|---------------------------------------------|--------------------|
| `Classificacao\s*\|\s*`(\w+)``             | `Classificação` \| `MAJOR`                  | `change_type` → "unknown" |
| `Iteracao proposta\s*\|\s*`(v[\d.]+)``     | `Iteração proposta` \| `v2.0`               | `iteration` → None |
| `"PRPs Existentes com Alteracao (PRP-A)"`  | `PRPs Existentes com Alteração (PRP-A)`     | `affected_prps` → [] |
| `"Novos PRPs Necessarios (PRP-N)"`         | `Novos PRPs Necessários (PRP-N)`            | `new_prps` → [] |

**Reprodução:** ver §4.3 — DELTA_REPORT minimal com headers do template produz `affected_prps=[]`, `new_prps=[]`, `change_type="unknown"`, `iteration=None`.

**Impacto:** `llc delta plan` exibe plano sem PRPs afetados/novos; `iteration` não propaga para skip notes. A rastreabilidade brownfield (PRP-A, PRP-N) é perdida. O pipeline ainda executa via `skip_steps`, mas a visibilidade gerencial fica cega.

**Correção proposta:** Normalizar acentos no parser (usar `unicodedata.normalize('NFKD', ...)` ou regex insensível a acento), OU alinhar o template para ASCII. Recomenda-se tornar o parser robusto a acentos (datetime-seguro) já que o template é a fonte que o agente seguirá.

---

### F-05 — MEDIUM: Parser skip_steps captura linha de cabeçalho

**Localização:** `.ace/scripts/llc_delta/report.py:71-79`

```python
if in_skip and stripped.startswith("|") and not stripped.startswith("|---"):
    parts = [p.strip() for p in stripped.split("|")[1:-1]]
    if parts and len(parts) >= 2:
        skip_entry = {"step_id": parts[0].strip(), ...}
        result["skip_steps"].append(skip_entry)
```

Diferente do bloco `execute_steps` (linha 68: `if step_id and not step_id.startswith("Step")`), o bloco `skip_steps` **não filtra a linha de cabeçalho** "Step | Justificativa | Artefatos Reaproveitados". Resultado: `skip_steps` inclui `{"step_id": "Step", "reason": "Justificativa", ...}`.

**Impacto:** Baixo (o cabeçalho "Step" não canonicaliza para nenhum step real, então `is_step_skipped` não faz match falso), mas polui a saída de `llc delta plan` e é inconsistente com `execute_steps`.

**Correção proposta:** Adicionar `if parts[0].startswith("Step"): continue` no bloco skip, ou filtrar `not parts[0].lower() == "step"`.

---

### F-06 — MEDIUM: Definição duplicada de `gate` em `llc/cli.py`

**Localização:** `.ace/scripts/llc/cli.py:239-250` (primeira) e `llc/cli.py:279-304` (segunda)

```python
@cli.command()          # L239 — comando simples
@click.option("--step", ...)
def gate(step):
    """Exibe o checklist do gate para revisao manual."""
    decision = gate_check(step, None)
    ...

@cli.group()             # L279 — GRUPO (sobrescreve o comando acima)
def gate():
    """Comandos de gate (validacao humana)."""
    pass
```

Click registra o segundo `gate` (grupo), sombreando o primeiro. `llc gate --step 5` agora falha ("No such option: --step"). O subcomando `gate-checklist` é adicionado ao grupo (L304).

**Reprodução:**
```
$ python3 llc.py gate --step 5
Error: No such option: --step Did you mean --help?
```

**Impacto:** O comando standalone `llc gate --step N` é dead code. Funcionalmente os subcomandos `gate run/list/gate-checklist` existem, mas a superfície CLI é confusa e há código morto.

**Correção proposta:** Remover a primeira definição (L239-250) — é totalmente substituída por `gate run --gate`. Ou renomear para `gate show`.

---

### F-07 — MEDIUM: Inconsistência de case entre `_get_gate_id` e `normalize_step`

**Localização:** `.ace/scripts/llc/gates_meta.py:69-71` vs `.ace/scripts/llc_steps/normalize.py:23-33`

`_get_gate_id` faz `gate_name.lower()`:
```python
def _get_gate_id(gate_name: str) -> str:
    return GATE_ALIASES.get(gate_name.lower(), gate_name)
```
Mas `normalize_step` **não faz lowercase** — comparações contra REGISTRY e `_ALIAS_MAP` são exatas.

**Reprodução:**
```
normalize_step("security")  → id=10.6 (alias minúsculo casa)
normalize_step("Security")  → UnknownStepError (case não casa)
normalize_step("SECURITY")  → UnknownStepError
```

**Impacto:** `llc run --step Security` falha, embora `llc gate run --gate Security` (via `_get_gate_id` lowercasing) chegue a `gate_check("11-SEC")` que então crasha por F-02. Comportamento de case inconsistente entre os dois caminhos.

**Correção proposta:** Tornar `normalize_step` case-insensitive (lowercase antes de procurar em REGISTRY/_ALIAS_MAP), já que `_get_gate_id` e a docstring do REGISTRY sugerem insensibilidade.

---

### F-08 — MEDIUM: Skill órfã `llc-step-0-greenfield.md`

**Localização:** `.ace/scripts/llc_steps/registry.py:6` (step "0" com `skill_file=None`) vs `docs/skills/llc-step-0-greenfield.md` (existente)

Step "0" (Ingestão) e "0.1" (Conversão Docling) têm `skill_file=None` e `in_pipeline=False`. `llc run --step 0` → `skill_load` → "Step 0 não tem skill associada" → `sys.exit(1)`. Mas `docs/skills/llc-step-0-greenfield.md` existe e descreve exatamente a ingestão greenfield.

**Impacto:** A skill de ingestão greenfield não é alcançável via harness. Usuário precisa invocá-la manualmente (`@llc-step-0-greenfield`), fora do `llc run`. Inconsistente com o princípio "cada step aponta para uma skill_file exata" (skill.py:46).

**Correção proposta:** Wirear `skill_file="llc-step-0-greenfield"` no step "0" do REGISTRY (e `llc-step-0-1` já está wireado em 0.1). Decidir se step 0 entra no pipeline (`in_pipeline`) ou permanece manual.

---

### F-09 — MEDIUM: `AGENTS.md` ausente do repo root

**Localização:** `.ace/scripts/llc_harness/skill.py:13-17` (`AGENTS_FILE = Path("AGENTS.md")`)

`load_agents_conventions()` lê `AGENTS.md` (cwd-relativo) para extrair o "Documentation Index (Compressed)" e zonas vermelhas. O arquivo **não existe** no repo root (existe apenas `docs/templates/AGENTS_TEMPLATE.md`). A função retorna `""` silenciosamente quando `AGENTS_FILE.exists()` é False.

**Impacto:** Todo prompt montado por `skill_load` recebe `conventions = ""` → o agente não recebe o Document Index nem as zonas vermelhas/safety conventions. O "progressive disclosure" (R4) fica sem a camada de convenções. Silencioso — sem erro.

**Correção proposta:** Instanciar `AGENTS.md` no repo root a partir de `docs/templates/AGENTS_TEMPLATE.md`, OU fazer `load_agents_conventions` warnar alto quando AGENTS.md falta, OU apontar `AGENTS_FILE` para o template como fallback.

---

### F-10 — LOW: Template DELTA_REPORT refere gate "10-COVERAGE" inexistente em gates.json

**Localização:** `docs/templates/DELTA_REPORT_TEMPLATE.md:134`

```
| 10.8 | `llc-step-10-8-test-coverage` | Cobertura (sempre) | 👤 10-COVERAGE |
```
gates.json key é `"10.8"` (não `"10-COVERAGE"`). O alias `"10-coverage"` existe em GATE_ALIASES mas não é uma gate-key de gates.json.

**Correção proposta:** Alterar `👤 10-COVERAGE` → `👤 10.8` no template.

---

### F-11 — LOW: Mensagem quickstart enganosa

**Localização:** `.ace/scripts/llc/cli.py:178-181`

```python
print("Gates incluídos: 1 (Visão), 4 (PRPs), 11 (Execução)")
```
Mas `pipeline_steps('0.5','11')` = 16 steps (inclui gates 2,3,5,6,7,8,9,10,11-SEC,12-NULL,10.8,11.5).

**Correção proposta:** Reformular para "Modo quickstart: pipeline completo 0.5→11 (16 gates), sem OWASP/PRP-Verify/Arch-Fitness" ou similar.

---

### F-12 — LOW: Help text sugere cwd errado

**Localização:** `.ace/scripts/llc_wave/run.py:78`

```
"Certifique-se de estar executando a partir de .ace/scripts/:\n"
"  cd .ace/scripts && python llc.py wave run --wave {wave_num}"
```
Mas paths cwd-relativos (`SKILLS_DIR=docs/skills`, `DELTA_REPORT_PATH=docs/planning/...`, `.ace/index.json`, `EXECUTION_WAVES_FILE=docs/planning/EXECUTION_WAVES.md`) exigem **repo root**, não `.ace/scripts/`.

**Correção proposta:** "Execute a partir do repo root: python .ace/scripts/llc.py wave run --wave N".

---

### F-13 — LOW: Geração de cobertura em prp_verify é JS-only

**Localização:** `.ace/scripts/prp_verify/coverage.py:36-64`

`check_project_coverage` tenta `npx vitest run --coverage` depois `npx jest --coverage` (timeout 120s cada). Projetos Python/Go sem node/npx: `FileNotFoundError` capturado → WARN `coverage_not_generated`. Não bloqueia merge (exit 1, não 2), mas o tente-gerar é desperdício para stacks não-JS.

**Correção proposta:** Detectar stack (presença de `package.json`/`pyproject.toml`/`go.mod`) e só tentar a ferramenta de cobertura relevante; caso contrário pular direto para WARN.

---

### F-14 — LOW: Sub-skills 5a/5b/5c/11a/11b/8b não cabeadas (D-02)

**Localização:** `docs/skills/llc-step-5a/5b/5c/11a/11b/8b-*.md` (existem) vs `llc_steps/registry.py` (não referenciadas)

`llc-step-11.md:13` declara "Step 11a (Domain Modeling - obrigatório pré-execution), Step 11b (Arch Fitness - obrigatório no PRP Verify)" como sub-steps, e `:31-34` lista pré-requisitos "Step 5a", "Step 8b", "Step 11a". Estas skills existem em `docs/skills/` mas não têm entries no REGISTRY — são inalcançáveis via `llc run`.

**Status:** Corresponde ao item **D-02** previamente classificado out-of-scope (trabalho in-flight revertido). Mantém-se como LOW/info: não é um defect de regressão, mas é uma divergência semântica entre o que `llc-step-11.md` exige e o que o pipeline oferece.

**Correção proposta:** (decisão de produto) wirear as sub-skills como steps no REGISTRY, ou remover as referências de pré-requisito de `llc-step-11.md` até que sejam cabeadas.

---

## 6. Cross-Check Matricial: gates.json × REGISTRY × GATE_ALIASES × Templates

| Gate key (gates.json) | step (gates.json) | REGISTRY step id | REGISTRY gate | GATE_ALIASES | Template ref | Consistente? |
|-----------------------|-------------------|------------------|---------------|--------------|--------------|--------------|
| 1  | 0.5 | 0.5  | "1"  | — | — | ✅ |
| 2  | 1   | 1    | "2"  | — | — | ✅ |
| 3  | 2   | 2    | "3"  | — | — | ✅ |
| 4  | 3   | 3    | "4"  | — | — | ✅ |
| 5  | 4   | 4    | "5"  | — | — | ✅ |
| 6  | 5   | 5    | "6"  | — | — | ✅ |
| 7  | 6   | 6    | "7"  | — | — | ✅ |
| 8  | 7   | 7    | "8"  | — | — | ✅ |
| 9  | 8   | 8    | "9"  | — | — | ✅ |
| 10 | 9   | 9    | "10" | — | — | ✅ |
| 11 | 10  | 10   | "11" | — | — | ✅ |
| 11.5 | 10.5 | 10.5 | "11.5" | — | — | ✅ |
| 11-SEC | 10.6 | 10.6 | "11-SEC" | security→"11-SEC" | — | ✅ mapeamento, ❌ execução (F-02) |
| 11-OWASP | 11.1 | 11.1 | "11-OWASP" | owasp→"11-OWASP" | — | ✅ mapeamento, ❌ execução (F-02) |
| 12-NULL | 10.7 | 10.7 | "12-NULL" | null-safety→"12-NULL" | — | ✅ mapeamento, ❌ execução (F-02) |
| 10.8 | 10.8 | 10.8 | "10.8" | test-coverage/10-coverage→"10.8" | "10-COVERAGE" (F-10) | ✅ mapeamento, ⚠️ template (F-10) |
| 11-VERIFY | 11.2 | 11.2 | "11-VERIFY" | verify→"11.2" | — | ✅ |
| 11-ARCH | 11.3 | 11.3 | "11-ARCH" | (arch→"arch" via alias step) | — | ✅ |
| **Δ.0** | 0.2 | 0.2 | **None** | — | — | ❌ **F-03** (gate não wireado) |
| **Δ.1** | 0.3 | 0.3 | **None** | — | — | ❌ **F-03** (gate não wireado) |

**Veredito:** 2 gates delta (Δ.0/Δ.1) definidos em gates.json mas não wireados no REGISTRY (F-03); 3 gate-aliases crasham em execução (F-02); 1 referência de template incorreta (F-10). Demais mapeamentos consistentes.

---

## 7. Lacunas de Teste (causam F-01 passar despercebido)

| Caminho de runtime                | Coberto por teste? | Risco |
|-----------------------------------|--------------------|-------|
| `SCRIPTS_DIR` aponta para dir real | ❌ não | F-01 invisível |
| `load_gates_config` carrega gates.json real | ❌ não | gates.json vazio invisível |
| `session_start` subprocess real | ❌ não (mock) | init broken invisível |
| `session_end` subprocess real | ❌ não (mock) | finalize broken invisível |
| `gate_check` com gate-key (11-SEC) | ❌ não | F-02 invisível |
| `parse_delta_report` com template acentuado | ❌ não | F-04 invisível |

**Recomendação:** Adicionar characterization tests que exercitem paths reais (sem mock de `SCRIPTS_DIR`/`GATES_FILE`) e um fixture `DELTA_REPORT` acentuado idêntico ao template.

---

## 8. Plano de Correção Sugerido (ordenado por prioridade)

### P0 — Bloqueia runtime (corrigir antes de tudo)
1. **F-01:** Corrigir `llc_harness/common.py` paths (off-by-one). Adicionar teste characterization de paths reais + gates.json carregado.
2. **F-02:** Adicionar fallback de gate-key em `get_gate_checklist`. Adicionar teste `gate_check("11-SEC")`/`"12-NULL"`/`"11-OWASP"`.

### P1 — Semântico de gates/delta (corrigir após P0)
3. **F-03:** Wirear gates Δ.0/Δ.1 no REGISTRY (steps 0.2/0.3). Teste: `gate_check("0.2")` mostra checklist Δ.0.
4. **F-04:** Tornar `parse_delta_report` robusto a acentos. Teste com fixture acentuado do template.

### P2 — Consistência/UX
5. **F-06:** Remover `gate` command duplicado em `cli.py` (L239-250).
6. **F-07:** Tornar `normalize_step` case-insensitive.
7. **F-08:** Wirear `llc-step-0-greenfield` no step "0" do REGISTRY (ou documentar step 0 como manual-only).
8. **F-09:** Instanciar `AGENTS.md` no repo root ou warnar alto na ausência.

### P3 — Polish
9. **F-05:** Filtrar header row em skip_steps parser.
10. **F-10:** Corrigir "10-COVERAGE" → "10.8" no template DELTA_REPORT.
11. **F-11:** Corrigir mensagem quickstart.
12. **F-12:** Corrigir help text cwd (repo root, não .ace/scripts).
13. **F-13:** Detectar stack antes de tentar cobertura JS em prp_verify.
14. **F-14:** (decisão de produto) wirear sub-skills 5a/5b/5c/11a/11b/8b ou remover pré-requisitos de llc-step-11.md.

---

## 9. Verificação Pós-Correção (critérios de aceite)

- `python3 -c "from llc_harness.common import SCRIPTS_DIR, GATES_FILE; assert SCRIPTS_DIR.exists() and GATES_FILE.exists()"` passa.
- `python3 llc.py run --step 5 --task "test"` (com agente mockado) completa init→skill→gate→finalize sem crash.
- `python3 llc.py gate run --gate security` (dry-run e real) mostra checklist e pede A/R sem crash.
- `python3 llc.py gate run --gate null-safety` e `--gate owasp` idem.
- `parse_delta_report()` com conteúdo acentuado do template retorna `change_type`, `iteration`, `affected_prps`, `new_prps` não-vazios.
- `gate_check("0.2")` e `gate_check("0.3")` mostram checklists Δ.0/Δ.1.
- Suíte existente: 67 passed mantidos + novos characterization tests de paths/gate-keys/delta-accents.
