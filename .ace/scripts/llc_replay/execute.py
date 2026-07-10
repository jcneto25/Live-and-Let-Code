import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from .constants import LOGS_DIR
from .zones import substitute


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
