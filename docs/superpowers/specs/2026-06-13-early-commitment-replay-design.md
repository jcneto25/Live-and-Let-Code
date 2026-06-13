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

## 7. Controle de Versao

| Versao | Data | Autor | Alteracoes |
|--------|------|-------|------------|
| 1.0.0 | 13/06/2026 | Equipe LLC | Versao inicial: Early Commitment (4 tipos) + Deterministic Replay engine |
