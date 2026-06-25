#!/usr/bin/env python3
"""
Valida a estrutura de tags XML nos arquivos de sessão ACE.

Verifica:
- Tags balanceadas (abertura/fechamento)
- context_seed presente + schema de 4 campos em sessões completed
- Atributos obrigatórios e valores válidos
- Front matter YAML
- index.json íntegro

Uso:
    python .ace/scripts/validate-tags.py
    python .ace/scripts/validate-tags.py --fix
    python .ace/scripts/validate-tags.py --session 2026-06-09-001
    python .ace/scripts/validate-tags.py --strict --json
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"

BALANCED_TAGS = [
    "action_log", "action", "thinking", "learning_point",
    "gate_result", "blocker", "context_seed", "skill_feedback",
    "file_delta", "description", "lines_changed", "result"
]

REQUIRED_ATTRS = {
    "action": ["type"],
    "gate_result": ["step", "decision"],
    "learning_point": ["priority"],
    "blocker": ["resolved"],
    "skill_feedback": ["skill"]
}

VALID_VALUES = {
    "action": {"type": ["git_commit", "file_create", "file_modify", "file_delete", "test_run", "tool_call"]},
    "gate_result": {"decision": ["approved", "rejected", "conditional"]},
    "learning_point": {"priority": ["high", "medium", "low"]},
    "blocker": {"resolved": ["true", "false"]},
    "skill_feedback": {"priority": ["high", "medium", "low"]}
}

CONTEXT_SEED_FIELDS = ["state", "pending", "blockers", "next_action"]


class ValidationError:
    def __init__(self, file: str, line: int, message: str, fixable: bool = False):
        self.file = file; self.line = line; self.message = message; self.fixable = fixable


def validate_yaml_front_matter(content: str, file_path: Path) -> list:
    errors = []
    if not content.startswith("---"):
        errors.append(ValidationError(str(file_path), 1, "Front matter YAML não encontrado"))
        return errors
    end_match = re.search(r'\n---\n', content[3:])
    if not end_match:
        errors.append(ValidationError(str(file_path), 1, "Front matter YAML não fechado"))
        return errors
    yaml_content = content[3:end_match.start() + 3]
    for field in ["session_id", "llc_step", "status"]:
        if f"{field}:" not in yaml_content:
            errors.append(ValidationError(str(file_path), 1,
                          f"Campo obrigatório '{field}' não encontrado no front matter"))
    return errors


def validate_balanced_tags(content: str, file_path: Path) -> list:
    errors = []
    for tag in BALANCED_TAGS:
        open_count = len(re.findall(f'<{tag}[\\s>]', content))
        close_count = len(re.findall(f'</{tag}>', content))
        if open_count != close_count:
            line_num = 1
            for i, line in enumerate(content.split('\n'), 1):
                if f'<{tag}' in line or f'</{tag}>' in line:
                    line_num = i; break
            errors.append(ValidationError(str(file_path), line_num,
                f"Tag <{tag}> desbalanceada: {open_count} abertura(s), {close_count} fechamento(s)", fixable=True))
    return errors


def validate_required_attributes(content: str, file_path: Path) -> list:
    errors = []
    for tag, attrs in REQUIRED_ATTRS.items():
        for match in re.finditer(f'<{tag}([^>]*)>', content):
            attrs_str = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            for attr in attrs:
                if f'{attr}=' not in attrs_str:
                    errors.append(ValidationError(str(file_path), line_num,
                        f"Tag <{tag}> sem atributo obrigatório '{attr}'"))
    return errors


def validate_attribute_values(content: str, file_path: Path) -> list:
    errors = []
    for tag, attr_validations in VALID_VALUES.items():
        for match in re.finditer(f'<{tag}([^>]*)>', content):
            attrs_str = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            for attr, valid_values in attr_validations.items():
                attr_match = re.search(f'{attr}="([^"]*)"', attrs_str)
                if attr_match and attr_match.group(1) not in valid_values:
                    errors.append(ValidationError(str(file_path), line_num,
                        f"Tag <{tag}> com valor inválido para '{attr}': '{attr_match.group(1)}'. Válidos: {valid_values}"))
    return errors


def validate_context_seed(content: str, file_path: Path, status: str) -> list:
    errors = []
    if status != "completed":
        return errors
    if "<context_seed>" not in content:
        errors.append(ValidationError(str(file_path), 1, "completed sem <context_seed>", fixable=True))
        return errors
    if "</context_seed>" not in content:
        errors.append(ValidationError(str(file_path), 1, "<context_seed> não fechado", fixable=True))
        return errors
    match = re.search(r'<context_seed>(.*?)</context_seed>', content, re.DOTALL)
    if match:
        seed = match.group(1).strip()
        for field in CONTEXT_SEED_FIELDS:
            if not re.search(rf'^{field}:', seed, re.MULTILINE):
                errors.append(ValidationError(str(file_path), 1,
                    f"<context_seed> sem campo obrigatório '{field}'", fixable=True))
    return errors


def validate_index_json() -> list:
    errors = []
    if not INDEX_FILE.exists():
        errors.append(ValidationError(str(INDEX_FILE), 1, "index.json não encontrado"))
        return errors
    try:
        index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        errors.append(ValidationError(str(INDEX_FILE), 1, f"index.json inválido: {e}"))
        return errors
    if "sessions" not in index:
        errors.append(ValidationError(str(INDEX_FILE), 1, "index.json sem campo 'sessions'"))
    return errors


# Arquivos de meta/config na raiz que não exigem sessão (commits triviais).
_META_FILES = {
    ".gitignore", ".gitattributes", ".pre-commit-config.yaml",
    ".editorconfig", "LICENSE", ".npmrc", ".nvmrc",
}


def _staged_code_files() -> list:
    """Arquivos de código staged (git diff --cached). [] se não for git ou sem diff.

    Exclui meta/documentos: tudo sob .ace/ e docs/, arquivos .md e um pequeno
    conjunto de arquivos de configuração raiz. Commits só de docs/meta são livres.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=False,
        )
    except (FileNotFoundError, OSError):
        return []
    if result.returncode != 0:
        return []

    code_files = []
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        if path.startswith(".ace/") or path.startswith("docs/"):
            continue
        if path.endswith(".md"):
            continue
        if path in _META_FILES:
            continue
        code_files.append(path)
    return code_files


def _session_referenced_files() -> set:
    """Caminhos referenciados em <file_delta> de todas as sessões (heurística de cobertura)."""
    referenced: set = set()
    if not SESSIONS_DIR.exists():
        return referenced
    for session_file in SESSIONS_DIR.glob("*.md"):
        try:
            content = session_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in re.finditer(r"<file_delta>(.*?)</file_delta>", content, re.DOTALL):
            for tok in re.split(r"[\n,]+", m.group(1)):
                tok = tok.strip().strip("`").strip("*").strip()
                if tok:
                    referenced.add(tok)
    return referenced


def validate_session_coverage(strict: bool = False) -> list:
    """Garante que commits com código tenham sessão ACE registrada.

    Previne o modo de falha "trabalho feito fora do ciclo init→finalize": um commit
    que altera código mas não tem nenhuma sessão no .ace (`.ace/index.json` com
    `sessions: []`) não prova entrega incremental.

    - ERRO (bloqueia): diff staged em código + zero sessões in_progress/completed.
    - AVISO (erro só com strict): arquivos de código staged não citados em <file_delta>.
    """
    errors = []
    code_files = _staged_code_files()
    if not code_files:
        return errors  # commit só de docs/meta — nada a exigir

    sessions = []
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            sessions = [s for s in index.get("sessions", [])
                        if s.get("status") in ("in_progress", "completed")]
        except json.JSONDecodeError:
            pass

    if not sessions:
        errors.append(ValidationError(
            str(INDEX_FILE), 1,
            f"{len(code_files)} arquivo(s) de código no commit, mas nenhuma sessão ACE registrada. "
            "Enrole o trabalho numa sessão antes de commitar: "
            "`python .ace/scripts/initialize_session.py --step N --task \"...\"` "
            "(ou `python .ace/scripts/llc.py run --step N`).",
        ))
        return errors

    referenced = _session_referenced_files()
    uncovered = [f for f in code_files
                 if f not in referenced and Path(f).name not in referenced]
    if uncovered:
        shown = ", ".join(uncovered[:5])
        suffix = "…" if len(uncovered) > 5 else ""
        msg = (f"{len(uncovered)} arquivo(s) de código no commit não aparecem em <file_delta> "
               f"de nenhuma sessão ({shown}{suffix}). Confirme que há uma sessão aberta cobrindo este trabalho.")
        if strict:
            errors.append(ValidationError(str(INDEX_FILE), 1, msg))
        else:
            logger.warning("⚠️  %s", msg)
    return errors


def fix_unbalanced_tags(file_path: Path) -> bool:
    content = file_path.read_text(encoding='utf-8')
    fixed = False
    for tag in BALANCED_TAGS:
        open_count = len(re.findall(f'<{tag}[\\s>]', content))
        close_count = len(re.findall(f'</{tag}>', content))
        if open_count > close_count:
            content += f"\n</{tag}>" * (open_count - close_count)
            fixed = True
            logger.info(f"🔧 Adicionado(s) {open_count - close_count} fechamento(s) para <{tag}>")
    if fixed:
        file_path.write_text(content, encoding='utf-8')
    return fixed


def main():
    parser = argparse.ArgumentParser(description="Valida estrutura de tags XML em sessões ACE")
    parser.add_argument("--session", type=str, help="Valida apenas uma sessão")
    parser.add_argument("--fix", action="store_true", help="Tenta corrigir automaticamente")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 em qualquer erro")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--coverage", action="store_true",
                        help="Modo focado: verifica apenas cobertura de sessão (commit com código exige sessão ACE)")
    args = parser.parse_args()

    if args.coverage:
        cov_errors = validate_session_coverage()
        print(f"\n{'=' * 60}")
        print("🔒 COBERTURA DE SESSÃO ACE")
        print(f"{'=' * 60}")
        if cov_errors:
            for e in cov_errors:
                print(f"   ❌ {e.message}")
            print(f"\n❌ {len(cov_errors)} problema(s) — bloqueando o commit.")
        else:
            print("✅ Commit coberto por sessão ACE (ou commit só de docs/meta).")
        print(f"{'=' * 60}")
        return 1 if cov_errors else 0

    if args.session:
        session_files = [SESSIONS_DIR / f"{args.session}.md"]
    else:
        session_files = sorted(SESSIONS_DIR.glob("*.md")) if SESSIONS_DIR.exists() else []

    all_errors = validate_index_json()

    for session_file in session_files:
        if not session_file.exists():
            all_errors.append(ValidationError(str(session_file), 1, "Arquivo não encontrado"))
            continue
        content = session_file.read_text(encoding='utf-8')
        status_match = re.search(r'status:\s*"([^"]*)"', content)
        status = status_match.group(1) if status_match else "unknown"
        all_errors.extend(validate_yaml_front_matter(content, session_file))
        all_errors.extend(validate_balanced_tags(content, session_file))
        all_errors.extend(validate_required_attributes(content, session_file))
        all_errors.extend(validate_attribute_values(content, session_file))
        all_errors.extend(validate_context_seed(content, session_file, status))

    if not args.session:
        all_errors.extend(validate_session_coverage(strict=args.strict))

    fixable = [e for e in all_errors if e.fixable]
    non_fixable = [e for e in all_errors if not e.fixable]

    if args.json:
        print(json.dumps({
            "valid": len(all_errors) == 0,
            "total_errors": len(all_errors),
            "fixable": len(fixable),
            "non_fixable": len(non_fixable),
            "errors": [{"file": e.file, "line": e.line, "message": e.message, "fixable": e.fixable}
                        for e in all_errors]
        }, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"🔍 VALIDAÇÃO ACE — {len(session_files)} sessão(ões)")
        print(f"{'='*60}")
        if not all_errors:
            print("✅ Nenhum erro encontrado")
        else:
            if non_fixable:
                print(f"\n❌ ERROS ({len(non_fixable)}):")
                for e in non_fixable:
                    print(f"   ❌ {e.file}:{e.line} — {e.message}")
            if fixable:
                print(f"\n🔧 CORRIGÍVEIS ({len(fixable)}):")
                for e in fixable:
                    print(f"   🔧 {e.file}:{e.line} — {e.message}")
        print(f"{'='*60}")

    if args.fix and fixable:
        print("\n🔧 Aplicando correções...")
        for sf in session_files:
            if sf.exists():
                fix_unbalanced_tags(sf)
        print("✅ Correções aplicadas — re-execute para validar")

    return 1 if (args.strict and all_errors) else 0


if __name__ == "__main__":
    sys.exit(main())
