#!/usr/bin/env python3
"""code-health — análise de saúde estrutural via git history (git log/age)."""

import re
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def run_git_log(since: str) -> list[dict]:
    """Extrai log do git com --numstat para análise de churn."""
    cmd = [
        "git",
        "log",
        f"--since={since}",
        "--numstat",
        "--format=%H|%ai|%s",
        "--no-merges",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []

    commits = []
    current = None
    for line in result.stdout.strip().split("\n"):
        if "|" in line and not line.startswith((" ", "\t")):
            if current:
                commits.append(current)
            parts = line.split("|", 2)
            current = {
                "hash": parts[0][:8],
                "date": parts[1][:10],
                "message": parts[2],
                "files": [],
            }
        elif current and line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    deleted = int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    added = deleted = 0
                current["files"].append(
                    {"path": parts[2], "added": added, "deleted": deleted}
                )
    if current:
        commits.append(current)
    return commits


def classify_changes(commits: list[dict]) -> dict:
    """Classifica alterações em Added, Deleted, Modified, Moved, Copy/Pasted."""
    stats = {
        "added": 0,
        "deleted": 0,
        "modified": 0,
        "moved_min": 0,
        "moved_est": 0,
        "copy_est": 0,
    }
    new_files = set()
    modified_files = set()

    for c in commits:
        for f in c["files"]:
            path = f["path"]
            if "=>" in path and "{" in path:
                stats["moved_min"] += f["added"] + f["deleted"]
                new_files.add(path.split("=>")[-1].strip().rstrip("}").strip())
            elif f["added"] > 0 and f["deleted"] == 0:
                if path not in modified_files:
                    stats["added"] += f["added"]
                    new_files.add(path)
            elif f["deleted"] > 0 and f["added"] == 0:
                stats["deleted"] += f["deleted"]
            else:
                stats["modified"] += f["added"] + f["deleted"]
                modified_files.add(path)

    est_new = stats["added"] + stats["moved_min"]
    est_all = est_new + stats["modified"] + stats["deleted"]

    if est_all > 0:
        stats["pct_moved"] = round((stats["moved_min"] / est_all) * 100, 1)
        stats["pct_added"] = round((stats["added"] / est_all) * 100, 1)
        stats["pct_modified"] = round((stats["modified"] / est_all) * 100, 1)
    else:
        stats["pct_moved"] = stats["pct_added"] = stats["pct_modified"] = 0

    copy_count = 0
    if len(commits) >= 10:
        for i, c1 in enumerate(commits[:-1]):
            for c2 in commits[i + 1 : i + 5]:
                f1 = set(f["path"] for f in c1["files"] if f["added"] > 30)
                f2 = set(f["path"] for f in c2["files"] if f["added"] > 30)
                for p1 in f1:
                    for p2 in f2:
                        if p1 != p2 and Path(p1).stem == Path(p2).stem:
                            copy_count += 1
    stats["copy_est"] = copy_count

    return stats


def analyze_file_age(commits: list[dict]) -> dict:
    """Analisa idade dos arquivos modificados."""
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    total_mod = 0
    old_mod = 0

    for c in commits:
        for f in c["files"]:
            total_mod += f["added"] + f["deleted"]
            if c["date"] < cutoff:
                old_mod += f["added"] + f["deleted"]

    return {
        "total_lines_modified": total_mod,
        "lines_in_files_older_than_30d": old_mod,
        "pct_legacy_touched": round((old_mod / total_mod * 100), 1)
        if total_mod > 0
        else 0,
    }
