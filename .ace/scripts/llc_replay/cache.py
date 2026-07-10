import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from .constants import CACHE_DIR


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
