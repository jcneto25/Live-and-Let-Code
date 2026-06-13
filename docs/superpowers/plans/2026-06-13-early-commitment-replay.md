# Early Commitment + Deterministic Replay — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two modules — `llc_classify.py` (task classifier with Early Commitment) and `llc_replay.py` (Deterministic Replay engine with rollback, metrics, and gate integration) — and integrate them into the existing Thin Harness (`llc_harness.py`).

**Architecture:** Three new Python files and one modification to an existing file. The classifier and replay engine are independent modules invoked by `llc_harness.py`'s `agent_invoke()` — no new CLI commands needed. Metrics are logged to `.ace/logs/replay.jsonl` with a companion `replay_stats.py` script for reporting.

**Tech Stack:** Python 3.10+, `json`, `subprocess`, `pathlib`, `hashlib`, `datetime`, `os` (all stdlib). Optional: `sentence-transformers` for cosine similarity in match algorithm.

**Design Spec:** `docs/superpowers/specs/2026-06-13-early-commitment-replay-design.md`

---

## File Map

| File | Action | Lines | Responsibility |
|------|--------|:-----:|---------------|
| `.ace/scripts/llc_classify.py` | CREATE | ~120 | Task classifier — 4 types, XML output, dominant type for hybrid tasks |
| `.ace/scripts/llc_replay.py` | CREATE | ~300 | Replay engine — cache CRUD, match, execute, rollback, metrics, zone check |
| `.ace/scripts/replay_stats.py` | CREATE | ~60 | Metrics dashboard — hit rate, success rate, token/time savings |
| `.ace/scripts/llc_harness.py` | MODIFY | +40 | Integrate classify + replay into `agent_invoke()` |
| `FAQ.md` | MODIFY | +30 | Early Commitment + Replay FAQ question |
| `FAQ.en.md` | MODIFY | +30 | English version |

---

### Task 1: Create llc_classify.py

**Files:**
- Create: `.ace/scripts/llc_classify.py`

- [ ] **Step 1: Write the classifier module**

```python
#!/usr/bin/env python3
"""
LLC Task Classifier — Early Commitment engine.

Classifies a task description into one of 4 types using the LLM.
The classification collapses the search space BEFORE execution,
preventing the agent from exploring dead-end paths.

Taxonomy (Pareto: 4 types cover ~80% of repeatable tasks):
- crud_endpoint: API endpoint CRUD operations
- ui_component: UI component creation/modification
- validation_rule: Schema/field/input validation
- test_write: Test writing (unit, integration, E2E)
"""

import subprocess
import sys
import shutil
from typing import Optional


TASK_TYPES = {
    "crud_endpoint": "criar/alterar/deletar/listar endpoints de API",
    "ui_component": "criar/alterar componentes de interface (form, tabela, modal)",
    "validation_rule": "adicionar/alterar validacao em schema, campo ou sanitizacao",
    "test_write": "escrever testes unitarios, integracao ou E2E",
}

CONFIDENCE_THRESHOLD = 0.80


def detect_llm_client():
    """Detecta cliente CLI disponivel para o prompt de classificacao."""
    for client in ["claude", "opencode", "codex", "cursor"]:
        if shutil.which(client):
            return client
    return None


def build_classify_prompt(task_description):
    """Monta prompt de classificacao (~150 tokens)."""
    categories = "\n".join(
        f"- {t}: {d}" for t, d in TASK_TYPES.items()
    )
    return f"""Classifique a tarefa abaixo em uma destas 4 categorias.
Se a tarefa envolver multiplos aspectos (ex: "Criar endpoint com validacao"),
escolha o tipo que representa a MAIOR PARTE do esforco de codificacao.
Ex: "Criar endpoint de usuario com validacao de email" -> crud_endpoint

Categorias:
{categories}

Se nao se encaixar em nenhuma, retorne type="unknown".

Tarefa: {task_description}

Responda APENAS com XML:
<task_classification><type>...</type><confidence>0.XX</confidence>
<reasoning>...</reasoning></task_classification>"""


def classify_task(task_description, client=None):
    """Classifica uma task. Retorna dict ou None se falhar."""
    if client is None:
        client = detect_llm_client()

    prompt = build_classify_prompt(task_description)

    if client:
        result = subprocess.run(
            [client, "--prompt", prompt],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout
    else:
        return None  # Sem cliente CLI — nao classifica

    # Parse XML da resposta
    import re
    type_match = re.search(r"<type>(.*?)</type>", output)
    confidence_match = re.search(r"<confidence>(.*?)</confidence>", output)
    reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", output)

    if not type_match:
        return None

    task_type = type_match.group(1).strip()
    if task_type == "unknown" or task_type not in TASK_TYPES:
        return None

    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
    reasoning = reasoning_match.group(1) if reasoning_match else ""

    if confidence < CONFIDENCE_THRESHOLD:
        return None

    return {
        "type": task_type,
        "confidence": confidence,
        "reasoning": reasoning,
    }
```

- [ ] **Step 2: Commit**

```bash
git add .ace/scripts/llc_classify.py
git commit -m "feat: add llc_classify.py — task classifier with 4-type taxonomy (Pareto 80%)"
```

---

### Task 2: Create llc_replay.py

**Files:**
- Create: `.ace/scripts/llc_replay.py`

- [ ] **Step 1: Write the replay engine**

```python
#!/usr/bin/env python3
"""
LLC Deterministic Replay Engine.

Gerencia o ciclo: gravar -> buscar -> reproduzir execucoes aprovadas.
- Cache em .ace/cache/{type}.json com atomic writes (R6)
- Match por exact type + keyword overlap + cosine similarity opcional (A)
- Pre-flight check antes de cada write (C)
- Zone check para arquivos RED (R2)
- Gate steps mid-execucao para pausas humanas
- Rollback via git checkout em falha parcial (R5)
- Metricas em .ace/logs/replay.jsonl (D)
"""

import json
import subprocess
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


CACHE_DIR = Path(".ace/cache")
LOGS_DIR = Path(".ace/logs")

RED_ZONE_PATTERNS = [
    "**/schema.prisma", "**/migrations/**",
    "**/*.guard.ts", "**/*.strategy.ts",
    "**/auth/**", "**/middleware/**",
    ".env", ".env.*", "**/config/**",
    ".github/workflows/**", "**/ci.yml"
]

# ── Atomic Cache I/O (R6) ──

def atomic_cache_read(cache_file: Path) -> dict:
    temp = cache_file.with_suffix('.tmp')
    if temp.exists():
        temp.unlink()
    if not cache_file.exists():
        return {"type": cache_file.stem, "scripts": []}
    return json.loads(cache_file.read_text(encoding='utf-8'))


def atomic_cache_write(cache_file: Path, data: dict):
    temp = cache_file.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    os.replace(str(temp), str(cache_file))


# ── Cache CRUD ──

def load_cache(task_type: str) -> list:
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{task_type}.json"
    data = atomic_cache_read(cache_file)
    return data.get("scripts", [])


def record_script(task_type, steps, params_used, task_description,
                  architecture_version, target_files, gate_approved=True):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{task_type}.json"
    data = atomic_cache_read(cache_file)

    import uuid
    script = {
        "id": f"{task_type[:4]}-{uuid.uuid4().hex[:4]}",
        "type": task_type,
        "original_task_description": task_description,
        "architecture_version": architecture_version,
        "target_files": [
            {"path": f["path"], "hash": f["hash"]}
            for f in target_files
        ],
        "steps": steps,
        "params_used": params_used,
        "gate_approved": gate_approved,
        "usage_count": 0,
        "created": datetime.now().isoformat(),
        "last_used": None
    }

    data.setdefault("scripts", []).append(script)
    atomic_cache_write(cache_file, data)
    return script["id"]


# ── Match Algorithm (A) ──

def extract_entities(text: str) -> list:
    """Extrai palavras-chave do prompt."""
    return [w.lower() for w in text.replace('"', '').replace("'", '').split()
            if len(w) > 2 and w.isalpha()]


def find_best_script(task_type: str, task_description: str) -> Optional[dict]:
    scripts = load_cache(task_type)
    if not scripts:
        return None

    entities = extract_entities(task_description)
    best = None
    best_score = 0.0

    for script in scripts:
        params = set(script.get("params_used", []))
        if not params:
            keyword_score = 0.5
        else:
            keyword_score = len(params & set(entities)) / len(params)

        final_score = keyword_score

        if final_score > best_score:
            best_score = final_score
            best = script

    threshold = 0.60
    if best_score >= threshold:
        return best
    return None


# ── Zone & Stale Check ──

def get_architecture_version() -> str:
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        for line in claude_md.read_text().splitlines()[:5]:
            if "versao" in line.lower() or "version" in line.lower():
                return line.strip()
    return "v0.0.0"


def is_red_zone(file_path: str) -> bool:
    from fnmatch import fnmatch
    return any(fnmatch(file_path, p) for p in RED_ZONE_PATTERNS)


def check_target_files_stale(target_files: list) -> bool:
    for tf in target_files:
        path = Path(tf["path"])
        if not path.exists():
            return True
        current = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
        if current != tf["hash"]:
            return True
    return False


# ── Pre-flight (C) ──

def preflight_all_steps(script: dict, params: dict) -> bool:
    for step in script.get("steps", []):
        if step["action"] in ("insert_after", "insert_before",
                               "replace", "insert_in_node"):
            target = substitute(step.get("file", ""), params)
            if not Path(target).exists():
                return False
            if "pattern" in step:
                content = Path(target).read_text()
                pattern = substitute(step["pattern"], params)
                if pattern not in content:
                    return False
    return True


def substitute(text: str, params: dict) -> str:
    import re
    def repl(m):
        key = m.group(1)
        return params.get(key, m.group(0))
    return re.sub(r"\{\{(\w+)\}\}", repl, text or "")


# ── Replay Execution ──

def extract_files_from_script(script: dict) -> list:
    files = []
    for step in script.get("steps", []):
        if "file" in step:
            files.append(step["file"])
    return list(set(files))


def execute_step(step: dict, params: dict):
    action = step["action"]

    if action == "open":
        pass  # Arquivo sera editado pelos passos seguintes

    elif action == "write_file":
        file = substitute(step["file"], params)
        content = substitute(step.get("content", ""), params)
        Path(file).parent.mkdir(parents=True, exist_ok=True)
        Path(file).write_text(content, encoding='utf-8')

    elif action == "insert_after":
        file = substitute(step["file"], params)
        pattern = substitute(step["pattern"], params)
        code = substitute(step.get("code", ""), params)
        content = Path(file).read_text()
        idx = content.index(pattern) + len(pattern)
        new_content = content[:idx] + "\n" + code + content[idx:]
        Path(file).write_text(new_content, encoding='utf-8')

    elif action == "insert_in_node":
        file = substitute(step["file"], params)
        code = substitute(step.get("code", ""), params)
        content = Path(file).read_text()
        Path(file).write_text(content.rstrip() + "\n" + code + "\n")

    elif action == "replace":
        file = substitute(step["file"], params)
        old = substitute(step.get("old", ""), params)
        new = substitute(step.get("new", ""), params)
        content = Path(file).read_text()
        Path(file).write_text(content.replace(old, new))

    elif action == "run":
        command = substitute(step["command"], params)
        result = subprocess.run(command, shell=True, capture_output=True)
        expect = step.get("expect")
        if expect is not None:
            if expect == "pass" and result.returncode != 0:
                raise ReplayError(f"Expected pass, got exit {result.returncode}: {result.stderr[:200]}")
            if expect == "fail" and result.returncode == 0:
                raise ReplayError("Expected fail, got exit 0")
            if isinstance(expect, int) and result.returncode != expect:
                raise ReplayError(f"Expected exit {expect}, got {result.returncode}")

    elif action == "gate":
        pass  # Tratado no fluxo principal (deterministic_replay)

    else:
        raise ReplayError(f"Unknown action: {action}")


class ReplayError(Exception):
    pass


def deterministic_replay(script: dict, params: dict,
                          gate_check_fn, llm_fallback_fn, prompt, client):
    """Executa replay com rollback (R5), gate mid-execucao e metricas."""
    import time
    start = time.time()

    target_files = extract_files_from_script(script)

    try:
        for i, step in enumerate(script["steps"]):
            if step["action"] == "gate":
                msg = substitute(step.get("message", "Continuar?"), params)
                if gate_check_fn("replay_mid_execution", msg) != "approved":
                    raise ReplayError(f"Gate reprovado no step {i}")

            execute_step(step, params)

        duration_ms = int((time.time() - start) * 1000)
        log_replay_event("replay_success", script["id"],
                         steps_executed=len(script["steps"]),
                         duration_ms=duration_ms)

        script["usage_count"] = script.get("usage_count", 0) + 1
        script["last_used"] = datetime.now().isoformat()
        return {"status": "success"}

    except ReplayError as e:
        subprocess.run(["git", "checkout", "--"] + target_files, check=False)
        subprocess.run(["git", "clean", "-fd"], check=False)

        log_replay_event("replay_rollback", script["id"],
                         failed_step=i, error=str(e))

        print(f"⚠️  Replay falhou no step {i}. Rollback executado. Fallback para LLM.")
        return llm_fallback_fn(prompt, client)


# ── Metrics (D) ──

def log_replay_event(event_type: str, script_id=None, **kwargs):
    LOGS_DIR.mkdir(exist_ok=True)
    event = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "script_id": script_id,
        **{k: str(v) for k, v in kwargs.items()}
    }
    log_file = LOGS_DIR / "replay.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event) + "\n")
```

- [ ] **Step 2: Commit**

```bash
git add .ace/scripts/llc_replay.py
git commit -m "feat: add llc_replay.py — deterministic replay engine with cache, rollback, metrics"
```

---

### Task 3: Create replay_stats.py

**Files:**
- Create: `.ace/scripts/replay_stats.py`

- [ ] **Step 1: Write the stats script**

```python
#!/usr/bin/env python3
"""LLC Replay Metrics Dashboard."""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

LOGS_FILE = Path(".ace/logs/replay.jsonl")

def main():
    if not LOGS_FILE.exists():
        print("Nenhum dado de replay encontrado. Execute algumas tarefas primeiro.")
        sys.exit(0)

    events = []
    for line in LOGS_FILE.read_text(encoding='utf-8').strip().split('\n'):
        if line:
            events.append(json.loads(line))

    since_days = 30
    cutoff = (datetime.now() - timedelta(days=since_days)).isoformat()
    events = [e for e in events if e.get("timestamp", "") >= cutoff]

    hits = sum(1 for e in events if e["event"] == "replay_hit")
    misses = sum(1 for e in events if e["event"] == "replay_miss")
    successes = sum(1 for e in events if e["event"] == "replay_success")
    rollbacks = sum(1 for e in events if e["event"] == "replay_rollback")
    llm_fallbacks = sum(1 for e in events if e["event"] == "llm_fallback")
    total = hits + misses

    print(f"\nReplay Stats (ultimos {since_days} dias):")
    print(f"- Total tarefas:     {total + llm_fallbacks}")
    print(f"- Classificadas:     {total} ({total/(total+llm_fallbacks)*100:.1f}%)" if total+llm_fallbacks > 0 else "- Classificadas:     0")
    print(f"- Hits:              {hits} ({hits/total*100:.1f}% das classificadas)" if total > 0 else "- Hits:              0")
    print(f"- Sucessos:          {successes} ({successes/hits*100:.1f}% dos hits)" if hits > 0 else "- Sucessos:          0")
    print(f"- Rollbacks:         {rollbacks} ({rollbacks/hits*100:.1f}%)" if hits > 0 else "- Rollbacks:         0")
    print(f"- Tokens economizados: ~{hits * 5000:,}")
    print(f"- Tempo economizado:   ~{hits * 15 // 60} minutos")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add .ace/scripts/replay_stats.py
git commit -m "feat: add replay_stats.py — metrics dashboard for hit/success/token rates"
```

---

### Task 4: Integrate into llc_harness.py

**Files:**
- Modify: `.ace/scripts/llc_harness.py`

- [ ] **Step 1: Add imports at the top**

Before the existing code block `# ── Agent CLI detection ──`, add:

```python
from pathlib import Path
from datetime import datetime

# ── Early Commitment + Replay imports ──
try:
    from llc_classify import classify_task
    from llc_replay import (
        find_best_script, deterministic_replay, record_script,
        log_replay_event, is_red_zone, check_target_files_stale,
        get_architecture_version, preflight_all_steps, extract_files_from_script,
        load_cache, ReplayError
    )
    CLASSIFY_REPLAY_AVAILABLE = True
except ImportError:
    CLASSIFY_REPLAY_AVAILABLE = False
```

- [ ] **Step 2: Replace the agent_invoke function**

Replace the existing `agent_invoke` function with:

```python
def agent_invoke(prompt, task_description=None, client=None):
    """Invoca cliente CLI com Early Commitment + Replay."""
    if not CLASSIFY_REPLAY_AVAILABLE:
        return _llm_invoke(prompt, client)

    # 1. Early Commitment: classificar tarefa
    classification = None
    if task_description:
        classification = classify_task(task_description, client)
        if classification:
            log_replay_event("classify", None,
                             type=classification["type"],
                             confidence=classification["confidence"])
            print(f"🏷️  Classificado: {classification['type']} "
                  f"(confianca: {classification['confidence']:.0%})")

    if classification:
        # 2. Buscar script no cache
        script = find_best_script(classification["type"], task_description)

        if script:
            log_replay_event("replay_hit", script["id"],
                             type=classification["type"],
                             usage_count=script.get("usage_count", 0),
                             match_score="computed")

            # 2a. Stale cache check (R3)
            if check_target_files_stale(script.get("target_files", [])):
                log_replay_event("llm_fallback", None, reason="stale_cache")
                print("⚠️  Script obsoleto (arquivos mudaram). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2b. Architecture version check (R3)
            current_arch = get_architecture_version()
            if script.get("architecture_version", "") != current_arch:
                log_replay_event("llm_fallback", None, reason="arch_changed")
                print("⚠️  Script obsoleto (arquitetura mudou). Fallback para LLM.")
                return _llm_invoke(prompt, client)

            # 2c. Zone check (R2)
            target_files = extract_files_from_script(script)
            if any(is_red_zone(Path(f)) for f in target_files):
                print("🔴 Zona VERMELHA detectada. Gate humano necessario.")
                if gate_check(11, script) != "approved":
                    log_replay_event("llm_fallback", None, reason="zone_red_rejected")
                    return _llm_invoke(prompt, client)

            # 2d. Pre-flight (C)
            if not preflight_all_steps(script, {}):
                log_replay_event("llm_fallback", None, reason="preflight_fail")
                return _llm_invoke(prompt, client)

            # 3. REPLAY (R5: rollback integrado)
            print(f"⚡ Replay: {classification['type']} "
                  f"(script {script['id']}, {script.get('usage_count', 0)} usos)")
            return deterministic_replay(
                script, {}, gate_check, _llm_invoke, prompt, client
            )
        else:
            log_replay_event("replay_miss", None,
                             type=classification["type"], reason="no_cache")

    # 4. Fallback: execucao normal via LLM
    log_replay_event("llm_fallback", None,
                     reason="no_classify" if not classification else "cache_miss")
    return _llm_invoke(prompt, client)


def _llm_invoke(prompt, client=None):
    """Execucao LLM normal (original)."""
    if client is None:
        client = detect_agent_client()

    if client:
        print(f"🤖 Invocando {client}...")
        result = subprocess.run(
            [client, "--prompt", prompt],
            capture_output=False,
            cwd=Path.cwd()
        )
        return "", result.returncode
    else:
        print("📋 Nenhum cliente CLI detectado. Modo manual:")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print("\nCole o prompt acima no seu cliente de IA.")
        return "", 0
```

- [ ] **Step 3: Commit**

```bash
git add .ace/scripts/llc_harness.py
git commit -m "feat: integrate Early Commitment + Replay into llc_harness agent_invoke"
```

---

### Task 5: Add FAQ entries (PT-BR + EN-US)

**Files:**
- Modify: `FAQ.md`
- Modify: `FAQ.en.md`

- [ ] **Step 1: Add to FAQ.md (PT-BR)**

Before the end of the file, add:

```markdown

---

## ⚡ Early Commitment + Deterministic Replay

### O LLC usa Early Commitment e Deterministic Replay?

Sim. A partir da versao 1.5.0, o Thin Harness inclui dois modulos que reduzem o custo de tarefas repetitivas em ate 99%:

**Early Commitment:** Antes de executar, o `llc_classify.py` classifica a tarefa em 4 tipos (crud_endpoint, ui_component, validation_rule, test_write). Isso colapsa o espaco de busca do agente e elimina caminhos de beco sem saida.

**Deterministic Replay:** Apos a primeira execucao aprovada por gate humano, o caminho de execucao (tool calls, codigo gerado, comandos) e gravado em `.ace/cache/{type}.json`. Tarefas futuras da mesma classificacao reproduzem o script deterministicamente, com custo de tokens proximo de zero.

| Metrica | Alvo |
|---------|:----:|
| Taxa de hit (tarefas com replay) | >60% |
| Taxa de sucesso (replays sem rollback) | >90% |
| Reducao de tokens por tarefa repetida | ~99% |
| Rollback em falha parcial | `git checkout` instantaneo |

**Ver metricas:** `python .ace/scripts/replay_stats.py`
```

- [ ] **Step 2: Add to FAQ.en.md (EN-US)**

```markdown

---

## ⚡ Early Commitment + Deterministic Replay

### Does LLC use Early Commitment and Deterministic Replay?

Yes. Starting from version 1.5.0, the Thin Harness includes two modules that reduce repetitive task costs by up to 99%:

**Early Commitment:** Before execution, `llc_classify.py` classifies the task into 4 types (crud_endpoint, ui_component, validation_rule, test_write). This collapses the agent's search space and eliminates dead-end paths.

**Deterministic Replay:** After the first human-gate-approved execution, the execution path (tool calls, generated code, commands) is recorded in `.ace/cache/{type}.json`. Future tasks of the same classification replay the script deterministically, with near-zero token cost.

| Metric | Target |
|--------|:------:|
| Hit rate (tasks with replay) | >60% |
| Success rate (replays without rollback) | >90% |
| Token reduction per repeated task | ~99% |
| Rollback on partial failure | Instant `git checkout` |

**View metrics:** `python .ace/scripts/replay_stats.py`
```

- [ ] **Step 3: Commit**

```bash
git add FAQ.md FAQ.en.md
git commit -m "docs: add Early Commitment + Deterministic Replay FAQ (PT-BR + EN-US)"
```
