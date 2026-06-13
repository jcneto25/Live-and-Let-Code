# Early Commitment + Deterministic Replay — Design Specification

**Versao:** 1.0.0
**Data:** 13 de Junho de 2026
**Status:** Design Aprovado
**Projeto:** Live and Let Code (LLC) — Early Commitment classifier + Deterministic Replay engine
**Autor:** Equipe LLC

---

## 1. Visao Geral

### 1.1 Problema

O Thin Harness orquestra steps do pipeline, mas cada execucao de tarefa custa o total de tokens do LLM — mesmo tarefas repetitivas (validar CPF, criar endpoint CRUD, gerar teste unitario) sao "redescobertas" do zero a cada execucao. O ACE grava o historico da sessao, mas nao o reutiliza como script executavel.

### 1.2 Solucao

Dois modulos novos integrados ao Thin Harness:

- **`llc_classify.py`** — Early Commitment: classifica a tarefa em 4 tipos ANTES da execucao, colapsando o espaco de busca do agente
- **`llc_replay.py`** — Deterministic Replay: grava caminhos de execucao aprovados por gate humano e os reproduz deterministicamente em tarefas futuras da mesma classificacao

### 1.3 Decisoes de Design

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Taxonomia | 4 tipos (A — minimalista) | Pareto: 4 tipos cobrem ~80% das tarefas repetidas. Expandir para 9+ tipos quando o cache estiver maduro |
| Threshold de classificacao | confidence >= 0.80 | Equilibrio entre falso-positivo (replay incorreto) e falso-negativo (LLM desnecessario) |
| Threshold de match | score >= 0.60 | Similaridade minima entre entidades da tarefa e params do script cacheado |
| Formato de classificacao | XML (`<task_classification>`) | Estruturado, parseavel, LLM-friendly — mesmo padrao do ACE |
| Cache location | `.ace/cache/{type}.json` | Versionado, append-only, um arquivo por tipo |
| Parametrizacao | `{{placeholders}}` com substituicao por regex | Simples, sem template engine. Placeholders extraidos dos params do classification XML |

---

## 2. Taxonomia de Tarefas

### 2.1 Os 4 Tipos

| Tipo | Descricao | Exemplos |
|------|-----------|----------|
| `crud_endpoint` | CRUD API endpoint | POST/GET/PUT/DELETE, listagem paginada, criacao de recurso, atualizacao, delecao |
| `ui_component` | Componente de interface | Formulario, tabela, modal, dashboard, navegacao |
| `validation_rule` | Regra de validacao | Validar CPF/CNPJ/email, schema refine, input sanitization |
| `test_write` | Escrita de testes | Teste unitario de service, teste de integracao de endpoint, teste E2E |

### 2.2 Formato de Classificacao

```xml
<task_classification>
  <type>validation_rule</type>
  <confidence>0.94</confidence>
  <reasoning>Usuario pede validacao de CPF no schema — padrao validation_rule</reasoning>
  <params>
    <param name="field">cpf</param>
    <param name="entity">cliente</param>
    <param name="target_file">schemas/cliente.schema.ts</param>
  </params>
</task_classification>
```

Se `type="unknown"` ou `confidence < 0.80`, a tarefa segue para execucao normal via LLM.

---

## 3. Arquitetura — Fluxo Modificado do `llc run`

```
llc run --step 11 --prp PRP-001
│
├─ 1. session_start()
├─ 2. skill_load()
│
├─ 3. llc_classify()  🆕
│   └─ Retorna classification XML
│
├─ 4. agent_invoke() (modificado)
│   ├─ type != "unknown" AND confidence >= 0.80?
│   │   ├─ Cache tem script para este type?
│   │   │   ├─ SIM → llc_replay(script, params)      ← DETERMINISTIC REPLAY
│   │   │   └─ NAO → llm_execute(prompt)
│   │   │              └─ Gate approved → llc_record() ← GRAVA CAMINHO
│   │   └─ NAO → llm_execute(prompt)
│   └─ Retorna output
│
├─ 5. gate_check()
└─ 6. session_end()
```

---

## 4. Modulo `llc_classify.py`

### 4.1 Responsabilidade

Classificar a tarefa ANTES da execucao do agente. O classifier envia um prompt curto (~150 tokens) ao LLM pedindo a classificacao XML.

### 4.2 Prompt de Classificacao

```
Classifique a tarefa abaixo em uma destas 4 categorias:
- crud_endpoint: criar/alterar/deletar/listar endpoints de API
- ui_component: criar/alterar componentes de interface (form, tabela, modal)
- validation_rule: adicionar/alterar validacao em schema, campo ou sanitizacao
- test_write: escrever testes unitarios, integracao ou E2E

Se nao se encaixar em nenhuma, retorne type="unknown".

Tarefa: {task_description}

Responda APENAS com XML no formato:
<task_classification><type>...</type><confidence>0.XX</confidence><reasoning>...</reasoning></task_classification>
```

### 4.3 API

```python
def classify_task(task_description, client=None):
    """Classifica tarefa em 4 tipos.
    Retorna dict: {type, confidence, reasoning, params} ou None se falhar."""
    ...

def extract_entities(task_description):
    """Extrai entidades do prompt para match de replay.
    Ex: "Valide CPF no campo cliente.documento"
        → ["cpf", "cliente", "documento"]"""
    ...
```

---

## 5. Modulo `llc_replay.py`

### 5.1 Responsabilidade

Gerenciar o ciclo: gravar → buscar → reproduzir. O motor de replay opera em 3 fases:

- **record(path):** apos execucao bem-sucedida com gate aprovado, grava o caminho de execucao como script parametrico
- **find_script(type, entities):** busca no cache o melhor script para a classificacao e entidades da tarefa
- **replay(script, params):** executa deterministicamente o script com substituicao de placeholders

### 5.2 Cache de Scripts

```
.ace/cache/
├── crud_endpoint.json
├── ui_component.json
├── validation_rule.json
└── test_write.json
```

Formato de cada entrada no cache:

```json
{
  "type": "validation_rule",
  "scripts": [
    {
      "id": "val-001",
      "pattern": "zod_schema_refine",
      "steps": [
        {"action": "open", "file": "{{target_file}}"},
        {"action": "insert_after", "pattern": "{{field}}: z.string()",
         "code": ".refine({{validator_fn}}, '{{field}} invalido')"},
        {"action": "run", "command": "npm test {{test_file}}"}
      ],
      "params_used": ["target_file", "field", "validator_fn", "test_file"],
      "gate_approved": true,
      "usage_count": 5,
      "created": "2026-06-13T15:30:00Z",
      "last_used": "2026-06-13T16:45:00Z"
    }
  ]
}
```

### 5.3 Actions Suportadas

| Action | Descricao | Exemplo |
|--------|-----------|---------|
| `open` | Abre arquivo para edicao | `{"action": "open", "file": "schemas/cliente.schema.ts"}` |
| `insert_after` | Insere codigo apos um padrao | `{"action": "insert_after", "pattern": ".string()", "code": ".refine(cpf, 'invalido')"}` |
| `insert_before` | Insere codigo antes de um padrao | Igual, mas antes |
| `replace` | Substitui um padrao por novo codigo | `{"action": "replace", "old": "...", "new": "..."}` |
| `run` | Executa comando shell | `{"action": "run", "command": "npm test"}` |
| `write_file` | Cria novo arquivo | `{"action": "write_file", "file": "tests/x.spec.ts", "content": "..."}` |

### 5.4 Algoritmo de Match

```python
def find_best_script(type, task_description):
    scripts = load_cache(type)
    if not scripts:
        return None

    entities = extract_entities(task_description)

    best = None
    best_score = 0
    for script in scripts:
        overlap = len(set(script["params_used"]) & set(entities))
        score = overlap / len(script["params_used"])
        if score > best_score:
            best_score = score
            best = script

    return best if best_score >= 0.6 else None
```

### 5.5 API

```python
def record(type, steps, params_used, gate_decision):
    """Grava script no cache se gate approved."""
    ...

def find_best_script(type, task_description):
    """Busca melhor script no cache. Retorna script ou None."""
    ...

def replay(script, params):
    """Executa script deterministico com substituicao parametrica."""
    ...

def substitute_params(script, params):
    """Substitui {{placeholders}} pelos valores em params."""
    ...
```

---

## 6. Integracao com o `llc_harness.py`

### 6.1 Modificacao no `agent_invoke`

```python
def agent_invoke(prompt, task_description, client=None):
    # 1. Early Commitment: classificar tarefa
    classification = classify_task(task_description)

    if classification and classification["type"] != "unknown" and classification["confidence"] >= 0.80:
        # 2. Buscar script no cache
        script = find_best_script(classification["type"], task_description)
        if script:
            print(f"⚡ Replay: {classification['type']} (script {script['id']}, {script['usage_count']} usos)")
            # 3. Executar replay deterministico
            result = replay(script, classification.get("params", {}))
            return result, 0

    # 4. Fallback: execucao normal via LLM
    output, code = llm_invoke(prompt, client)

    # 5. Se gate approved, gravar caminho para replay futuro
    if classification and classification["type"] != "unknown":
        # O caminho sera gravado apos gate_check aprovar
        pass  # record() chamado em session_end()

    return output, code
```

---

## 7. Riscos Criticos e Mitigacoes (v1.1.0)

### 7.1 R1 — String Matching Fragil

**Problema:** Actions `insert_after` ou `replace` baseadas em pattern (regex/string) sao frageis. Um comentario adicionado, formatacao alterada ou variacao minima no codigo faz o replay falhar silenciosamente ou corromper o arquivo.

**Mitigacao:**
- Actions de escrita usam `ast_node` em vez de `pattern` sempre que possivel.
- Se `ast_node` nao for viavel, o `pattern` e validado por **dry-run de busca** antes da execucao.
- Se o pattern nao for encontrado no dry-run, o replay **aborta imediatamente** e faz fallback para LLM.

```json
// Em vez disso (fragil):
{"action": "insert_after", "pattern": "{{field}}: z.string()", "code": ".refine(...)"}

// Use isso (robusto):
{"action": "insert_in_node", "node_id": "schema_field_{{field}}", "position": "after",
 "code": ".refine({{validator_fn}}, '{{field}} invalido')"}
```

### 7.2 R2 — Violacao das Zonas de Autonomia (RED Zone)

**Problema:** O AGENTS.md define que mudancas em Schema, Auth, CI/CD ou `.env` sao Zona VERMELHA e exigem confirmacao humana sempre. Um script em cache poderia modificar um schema sem gate humano — um backdoor de seguranca.

**Mitigacao:** `llc_replay.py` verifica a Zona de Autonomia dos arquivos alvo ANTES de executar o replay. Se QUALQUER arquivo no script pertence a Zona Vermelha, o replay e pausado e exige `gate_check()` explicito ANTES do replay iniciar.

**Diferenca entre zone check e `gate` step:**
- **Zone check (R2):** pre-replay — verifica se o script toca zonas RED e bloqueia/libera antes de executar
- **`gate` step:** mid-replay — pausa o script em um ponto especifico (ex: antes de `DROP TABLE`) para aprovacao humana

Zonas vermelhas detectadas por padrao de path:
```python
RED_ZONE_PATTERNS = [
    "**/schema.prisma", "**/migrations/**",
    "**/*.guard.ts", "**/*.strategy.ts",
    "**/auth/**", "**/middleware/**",
    ".env", ".env.*", "**/config/**",
    ".github/workflows/**", "**/ci.yml"
]
```

### 7.3 R3 — Cache Obsoleto (Stale Cache)

**Problema:** Um script gravado ha 2 meses pode aplicar padroes arquiteturais obsoletos (ex: projeto migrou de validacao manual para Zod), criando divida tecnica silenciosa.

**Mitigacao:** Metadados de validade no cache:

```json
{
  "id": "val-001",
  "architecture_version": "v2.1",
  "target_file_hash": "a1b2c3d4",
  "original_task_description": "Valide CPF no campo cliente.documento"
}
```

- `architecture_version`: lido do `CLAUDE.md` ou `package.json`. Se a versao atual for maior, script ignorado.
- `target_file_hash`: hash SHA256 do arquivo alvo no momento da gravacao. Se o hash atual for diferente (arquivo mudou), script ignorado.

**Refinamento (v1.1.1):** `target_file_hash` e um array de `target_files`, nao um unico hash. Scripts frequentemente modificam multiplos arquivos (controller + service + module + test).

```json
{
  "target_files": [
    {"path": "src/clientes/clientes.controller.ts", "hash": "a1b2c3"},
    {"path": "src/clientes/clientes.service.ts", "hash": "d4e5f6"},
    {"path": "src/clientes/clientes.module.ts", "hash": "g7h8i9"}
  ]
}
```

Validacao: se QUALQUER arquivo do array teve o hash alterado, o script e considerado obsoleto e o LLM assume.

```python
def check_target_files(script):
    for tf in script.get("target_files", []):
        if not Path(tf["path"]).exists():
            return False  # Arquivo foi deletado/renomeado
        current_hash = sha256(Path(tf["path"]).read_bytes()).hexdigest()[:8]
        if current_hash != tf["hash"]:
            return False  # Arquivo mudou, script obsoleto
    return True
```
- Ambos falhando → fallback para LLM.

### 7.4 R4 — Violacao do Protocolo TDD no test_write

**Problema:** O AGENTS.md exige o ciclo 🔴 RED → 🟢 GREEN → 🔵 REFACTOR. Um script de replay que escreve teste e codigo de uma vez viola a regra fundamental do projeto.

**Mitigacao:** Scripts do tipo `test_write` DEVEM incluir steps com semantica explicita de resultado:

```json
{
  "type": "test_write",
  "scripts": [{
    "id": "test-001",
    "steps": [
      {"action": "write_file", "file": "{{test_file}}", "content": "{{test_code}}"},
      {"action": "run", "command": "npm test -- {{test_file}}", "expect": "fail"},
      {"action": "write_file", "file": "{{source_file}}", "content": "{{source_code}}"},
      {"action": "run", "command": "npm test -- {{test_file}}", "expect": "pass"}
    ]
  }]
}
```

**Semantica de `expect`:**

| Valor | Significado | Comportamento |
|-------|------------|---------------|
| `"pass"` | Espera sucesso | `exit_code == 0` |
| `"fail"` | Espera falha (qualquer motivo) | `exit_code != 0` — cobre erro de compilacao (2), sintaxe (127), ou teste falhando (1) |
| `0` (numero) | Exit code especifico (legado) | `exit_code == N` — usar apenas quando necessario |

`expect: "fail"` expressa a **intencao** da fase RED, nao o mecanismo. Testes podem falhar por motivos diferentes (compilacao, sintaxe, assert) — todos validos para a fase RED.

### 7.5 R5 — Falha Parcial com Estado Inconsistente

**Problema:** Se o replay executa 3 steps com sucesso e o 4o falha (ex: `expect: "pass"` nao bate), os primeiros 3 steps ja modificaram o sistema. O fallback para LLM assume um estado inconsistente.

**Mitigacao:** Rollback instantaneo via Git. PRPs ja rodam em worktrees isolados — o blast radius e limitado. O rollback usa `git checkout` para reverter arquivos tracked e `git clean` para remover untracked criados pelo replay.

```python
def deterministic_replay(script, params):
    target_files = [substitute(f) for f in extract_files_from_script(script)]

    try:
        for i, step in enumerate(script["steps"]):
            # Gate mid-execucao: pausa para confirmacao humana
            if step["action"] == "gate":
                message = substitute(step.get("message", "Confirmar continuacao?"), params)
                decision = gate_check("replay_mid_execution", message)
                if decision != "approved":
                    raise ReplayError(f"Gate reprovado pelo usuario no step {i}")
                continue

            execute_step(step, params)
        return {"status": "success"}
    except ReplayError as e:
        subprocess.run(["git", "checkout", "--"] + target_files, check=False)
        subprocess.run(["git", "clean", "-fd"], check=False)
        print(f"⚠️  Replay falhou no step {i}. Rollback executado. Fallback para LLM.")
        return llm_invoke(prompt, client)
```

**Por que Git, nao snapshot manual:**

| Abordagem | Velocidade | Cobre untracked? | Custo |
|-----------|:---------:|:----------------:|:-----:|
| Hash + restore manual | Lento (I/O) | Nao | Alto |
| `git checkout -- {files}` | **Instantaneo** | **Sim** (+ `git clean`) | Zero (Git ja usado) |

O LLC ja depende de Git em todas as sessoes. Nao ha custo adicional. Para projetos sem Git (raro no LLC), fallback para backup de conteudo em memoria.

---

## 8. Refinamentos de Design (v1.1.0)

### 8.1 A — Algoritmo de Match Aprimorado

A formula original (`overlap / len(params_used)`) e substituida por 3 camadas:

```python
def find_best_script(type, task_description):
    scripts = load_cache(type)
    if not scripts:
        return None

    entities = extract_entities(task_description)

    for script in scripts:
        # Camada 1: Type exact match (obrigatorio)
        if script["type"] != type:
            continue

        # Camada 2: Keyword overlap
        keyword_score = len(set(script.get("params_used", [])) & set(entities))
        keyword_score /= max(len(script.get("params_used", [])), 1)

        # Camada 3: Contextual similarity (opcional — embedding leve)
        cosine_score = 0.0
        if EMBEDDING_MODEL_AVAILABLE:
            original = script.get("original_task_description", "")
            current = task_description
            if original:
                cosine_score = cosine_similarity(embed(original), embed(current))

        # Score combinado: 50% keyword + 50% cosine (se disponivel)
        if cosine_score > 0:
            final_score = (keyword_score * 0.5) + (cosine_score * 0.5)
        else:
            final_score = keyword_score

        if final_score > best_score:
            best_score = final_score
            best = script

    # Threshold: >= 0.75 com embedding, >= 0.60 sem
    min_score = 0.75 if EMBEDDING_MODEL_AVAILABLE else 0.60
    return best if best_score >= min_score else None
```

Embedding leve opcional: `all-MiniLM-L6-v2` via `sentence-transformers` (~80MB, rapido em CPU). Se nao instalado, fallback para keyword overlap puro.

### 8.2 B — Classifier para Tarefas Hibridas

Prompt atualizado para tarefas que envolvem multiplos aspectos:

```
Classifique a tarefa abaixo em uma destas 4 categorias.
Se a tarefa envolver multiplos aspectos (ex: "Criar endpoint com validacao"),
escolha o tipo que representa a MAIOR PARTE do esforco de codificacao.
Ex: "Criar endpoint de usuario com validacao de email" -> crud_endpoint
(a validacao e um sub-passo; o CRUD e a acao principal).

Categorias:
- crud_endpoint: criar/alterar/deletar/listar endpoints de API
- ui_component: criar/alterar componentes de interface (form, tabela, modal)
- validation_rule: adicionar/alterar validacao em schema, campo ou sanitizacao
- test_write: escrever testes unitarios, integracao ou E2E

Se nao se encaixar em nenhuma, retorne type="unknown".

Tarefa: {task_description}

Responda APENAS com XML:
<task_classification><type>...</type><confidence>0.XX</confidence>
<reasoning>...</reasoning></task_classification>
```

### 8.3 C — Pre-flight Check no Replay

Antes de executar QUALQUER acao de escrita (`insert`, `replace`, `write_file`), o motor verifica:

```python
def preflight_check(step):
    if step["action"] in ("insert_after", "insert_before", "replace", "insert_in_node"):
        target = substitute(step["file"])
        if not Path(target).exists():
            print(f"⚠️  Pre-flight: {target} nao existe. Fallback para LLM.")
            return False

        if "pattern" in step:
            content = Path(target).read_text()
            pattern = substitute(step["pattern"])
            if pattern not in content:
                print(f"⚠️  Pre-flight: pattern nao encontrado em {target}. Fallback para LLM.")
                return False

    return True
```

Se o pre-flight falhar para QUALQUER step do script, o replay inteiro e abortado e o LLM assume.

---

## 9. Schema de Cache Atualizado (v1.1.0)

```json
{
  "type": "validation_rule",
  "scripts": [
    {
      "id": "val-001",
      "pattern": "zod_schema_refine",
      "original_task_description": "Valide CPF no campo cliente.documento",
      "architecture_version": "v1.4.0",
      "target_files": [
        {"path": "schemas/cliente.schema.ts", "hash": "a1b2c3d4"}
      ],
      "steps": [
        {"action": "open", "file": "{{target_file}}"},
        {"action": "insert_in_node", "node_id": "schema_field_{{field}}",
         "position": "after", "code": ".refine({{validator_fn}}, '{{field}} invalido')"},
        {"action": "run", "command": "npm test {{test_file}}"}
      ],
      "params_used": ["target_file", "field", "validator_fn", "test_file"],
      "gate_approved": true,
      "zone_check_passed": true,
      "usage_count": 5,
      "created": "2026-06-13T15:30:00Z",
      "last_used": "2026-06-13T16:45:00Z"
    }
  ]
}
```

### Actions Suportadas (atualizado)

| Action | Descricao | Campos |
|--------|-----------|--------|
| `open` | Abre arquivo para edicao | `file` |
| `insert_in_node` | Insere codigo em um AST node | `node_id`, `position` (`before`/`after`/`end`), `code` |
| `insert_after` | Insere apos pattern (com dry-run obrigatorio) | `file`, `pattern`, `code` |
| `replace` | Substitui pattern (com dry-run obrigatorio) | `file`, `old`, `new` |
| `write_file` | Cria novo arquivo | `file`, `content` |
| `gate` | Pausa replay para aprovacao humana mid-execucao | `message` |
| `run` | Executa comando com resultado esperado | `command`, `expect` (`"pass"`/`"fail"`/numero) |

---

## 10. Fluxo Final do `agent_invoke` (atualizado)

```python
def agent_invoke(prompt, task_description, client=None):
    # 1. Early Commitment
    classification = classify_task(task_description)

    if classification and classification["type"] != "unknown" and classification["confidence"] >= 0.80:
        # 2. Buscar script no cache (match aprimorado)
        script = find_best_script(classification["type"], task_description)

        if script:
            # 3. Verificar cache validity (stale cache check)
            current_arch = get_architecture_version()
            if script.get("architecture_version") != current_arch:
                print("⚠️  Script obsoleto (versao de arquitetura mudou). Fallback para LLM.")
                return llm_invoke(prompt, client)

            # 4. Zone check (RED zone verification)
            target_files = extract_files_from_script(script)
            if any(is_red_zone(f) for f in target_files):
                print("🔴 Zona VERMELHA detectada. Aguardando gate humano...")
                if gate_check("replay_red_zone", script) != "approved":
                    print("Gate reprovado. Fallback para LLM.")
                    return llm_invoke(prompt, client)

            # 5. Pre-flight check
            if not preflight_all_steps(script, classification.get("params", {})):
                print("Pre-flight falhou. Fallback para LLM.")
                return llm_invoke(prompt, client)

            # 6. REPLAY
            print(f"⚡ Replay: {classification['type']} (script {script['id']}, {script['usage_count']} usos)")
            return deterministic_replay(script, classification.get("params", {}))

    # 7. Fallback: LLM normal
    return llm_invoke(prompt, client)
```

---

## 11. Controle de Versao

| Versao | Data | Autor | Alteracoes |
|--------|------|-------|------------|
| 1.1.0 | 13/06/2026 | Equipe LLC | Adicionadas mitigacoes de risco (R1-R4), refinamentos de design (A-C), e schema de cache expandido |
| 1.0.0 | 13/06/2026 | Equipe LLC | Versao inicial: Early Commitment (4 tipos) + Deterministic Replay engine |
