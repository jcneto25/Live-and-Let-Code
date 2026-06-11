#!/usr/bin/env python3
"""
Automatiza git bisect com comando de teste fornecido pelo agente.
Reporta o commit + diff que introduziu a regressão.

Uso:
    python .ace/scripts/git-bisect.py --good HEAD~20 --bad HEAD --test "pytest tests/auth/"
    python .ace/scripts/git-bisect.py --good abc123 --bad def456 --test "npm test -- --grep login"
    python .ace/scripts/git-bisect.py --good HEAD~50 --bad HEAD --test "python -m pytest" --ace-session 2026-06-10-001
    python .ace/scripts/git-bisect.py --json
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
SESSIONS_DIR = ACE_DIR / "sessions"


def run_git(*args, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def git_bisect_start(good: str, bad: str) -> None:
    logger.info(f"🔍 Iniciando git bisect: good={good}, bad={bad}")
    run_git("bisect", "start")
    run_git("bisect", "bad", bad)
    run_git("bisect", "good", good)


def git_bisect_run(test_command: str) -> subprocess.CompletedProcess:
    logger.info(f"🧪 Executando: git bisect run {test_command}")
    result = subprocess.run(
        ["git", "bisect", "run"] + test_command.split(),
        capture_output=True, text=True
    )
    logger.info(f"Bisect stdout:\n{result.stdout}")
    if result.stderr:
        logger.info(f"Bisect stderr:\n{result.stderr}")
    return result


def git_bisect_reset() -> None:
    subprocess.run(["git", "bisect", "reset"], capture_output=True, text=True)


def get_offending_commit() -> str | None:
    try:
        result = run_git("bisect", "log")
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("# first bad commit: ["):
                return line.split("[")[1].split("]")[0]
    except subprocess.CalledProcessError:
        pass
    return None


def get_commit_diff(commit_sha: str) -> str:
    result = run_git("show", "--stat", "--patch", commit_sha)
    return result.stdout


def get_commit_info(commit_sha: str) -> dict:
    result = run_git("log", "-1", "--format=%H||%an||%ae||%ai||%s", commit_sha)
    sha, author, email, date, subject = result.stdout.strip().split("||")
    return {
        "sha": sha,
        "author": author,
        "email": email,
        "date": date,
        "subject": subject
    }


def get_bisect_log() -> str:
    result = run_git("bisect", "log")
    return result.stdout


def append_action_to_session(session_id: str, commit_sha: str, test_command: str) -> None:
    session_file = SESSIONS_DIR / f"{session_id}.md"
    if not session_file.exists():
        logger.warning(f"⚠️  Sessão {session_id} não encontrada — action não registrada")
        return

    action_block = (
        f"\n<action type=\"git_bisect\">\n"
        f"  <description>git bisect: {test_command} — regressão em {commit_sha[:8]}</description>\n"
        f"</action>\n"
    )

    with open(session_file, "a", encoding="utf-8") as f:
        f.write(action_block)
    logger.info(f"📝 Action registrada na sessão {session_id}")


def main():
    parser = argparse.ArgumentParser(description="Automatiza git bisect para encontrar regressões")
    parser.add_argument("--good", type=str, required=True, help="Commit conhecido como bom (ex: HEAD~20)")
    parser.add_argument("--bad", type=str, required=True, help="Commit conhecido como ruim (ex: HEAD)")
    parser.add_argument("--test", type=str, required=True, help="Comando de teste (ex: 'pytest tests/auth/')")
    parser.add_argument("--ace-session", type=str, default=None,
                        help="Session ID para registrar action no ACE")
    parser.add_argument("--json", action="store_true", help="Output em JSON para tool calls")
    args = parser.parse_args()

    git_bisect_reset()

    try:
        git_bisect_start(args.good, args.bad)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": f"git bisect start falhou: {e.stderr}"}), file=sys.stderr)
        git_bisect_reset()
        sys.exit(1)

    bisect_result = git_bisect_run(args.test)

    offending_sha = get_offending_commit()
    bisect_log = get_bisect_log()
    git_bisect_reset()

    if offending_sha:
        diff = get_commit_diff(offending_sha)
        commit_info = get_commit_info(offending_sha)

        if args.ace_session:
            append_action_to_session(args.ace_session, offending_sha, args.test)

        result = {
            "success": True,
            "offending_commit": offending_sha,
            "commit_info": commit_info,
            "test_command": args.test,
            "bisect_log": bisect_log,
            "diff": diff,
            "diff_truncated": len(diff) > 3000,
        }

        logger.info(f"🎯 Regressão encontrada no commit {offending_sha[:8]} por {commit_info['author']}")
    else:
        logger.info("✅ Nenhum commit culpado identificado — bisect inconclusivo")
        result = {
            "success": False,
            "error": "Bisect inconclusivo — nenhum commit culpado identificado",
            "bisect_stdout": bisect_result.stdout,
            "bisect_stderr": bisect_result.stderr,
            "bisect_log": bisect_log,
        }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["success"]:
            ci = result["commit_info"]
            print(f"\n{'='*60}")
            print(f"🎯 REGRESSÃO ENCONTRADA")
            print(f"{'='*60}")
            print(f"Commit:  {ci['sha']}")
            print(f"Autor:   {ci['author']} <{ci['email']}>")
            print(f"Data:    {ci['date']}")
            print(f"Mensagem: {ci['subject']}")
            print(f"{'='*60}")
            print(f"\n📋 DIFF:")
            print(f"{'-'*60}")
            diff_output = result["diff"]
            if len(diff_output) > 4000:
                diff_output = diff_output[:4000] + "\n\n... (diff truncado — use --json para saída completa)"
            print(diff_output)
            print(f"{'-'*60}")
        else:
            print(f"\n{'='*60}")
            print(f"❌ BISECT INCONCLUSIVO")
            print(f"{'='*60}")
            print(f"Nenhum commit culpado identificado.")
            if bisect_result.stdout:
                print(f"\nStdout:\n{bisect_result.stdout[:2000]}")
            if bisect_result.stderr:
                print(f"\nStderr:\n{bisect_result.stderr[:2000]}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
