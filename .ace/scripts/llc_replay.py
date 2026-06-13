#!/usr/bin/env python3
"""
LLC Deterministic Replay Engine.

Gerencia o ciclo: gravar -> buscar -> reproduzir execucoes aprovadas.
- Cache em .ace/cache/{type}.json com atomic writes (R6)
- Match por exact type + keyword overlap (A)
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


# ── Zone & Stale Check (R2, R3) ──

def get_architecture_version() -> str:
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        for line in claude_md.read_text().splitlines()[:5]:
            if "versao" in line.lower() or "version" in line.lower():
                return line.strip()
    return "v0.0.0"


def is_red_zone(file_path) -> bool:
    from fnmatch import fnmatch
    return any(fnmatch(str(file_path), p) for p in RED_ZONE_PATTERNS)


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


class ReplayError(Exception):
    pass


def execute_step(step: dict, params: dict):
    action = step["action"]

    if action == "open":
        pass

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
        pass  # Tratado no fluxo principal

    else:
        raise ReplayError(f"Unknown action: {action}")


def deterministic_replay(script: dict, params: dict,
                          gate_check_fn, llm_fallback_fn, prompt, client):
    import time
    start = time.time()

    target_files = extract_files_from_script(script)

    try:
        for i, step in enumerate(script["steps"]):
            if step["action"] == "gate":
                msg = substitute(step.get("message", "Continuar?"), params)
                if gate_check_fn("replay_mid_execution", msg) != "approved":
                    raise ReplayError(f"Gate reprovado no step {i}")
                continue

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
