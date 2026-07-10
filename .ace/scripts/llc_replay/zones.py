import hashlib
from fnmatch import fnmatch
from pathlib import Path

from .constants import RED_ZONE_PATTERNS


# ── Zone & Stale Check (R2, R3) ──

def get_architecture_version() -> str:
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        for line in claude_md.read_text().splitlines()[:5]:
            if "versao" in line.lower() or "version" in line.lower():
                return line.strip()
    return "v0.0.0"


def is_red_zone(file_path) -> bool:
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
