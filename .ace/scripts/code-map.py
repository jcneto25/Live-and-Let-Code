#!/usr/bin/env python3
"""
Gera índice estrutural do codebase para grounding do agente.
Extrai: árvore de arquivos, assinaturas de funções/classes, imports, e dependências.

Sem dependências externas — usa apenas regex e git para extração.
O output é compacto (~3-8K tokens) para caber no context_seed ou ser carregado sob demanda.

Uso:
    python .ace/scripts/code-map.py                          # Mapa completo
    python .ace/scripts/code-map.py --max-depth 2            # Só diretórios de nível 2
    python .ace/scripts/code-map.py --include "src/**.ts"    # Só arquivos TypeScript em src/
    python .ace/scripts/code-map.py --signatures-only        # Só assinaturas (sem imports/árvore)
    python .ace/scripts/code-map.py --json                   # Output em JSON para tool calls
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {".git", ".ace", "node_modules", "__pycache__", ".venv", "venv",
                "dist", "build", ".next", ".turbo", "coverage", ".pytest_cache"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".pdf",
                ".lock", ".min.js", ".min.css", ".map"}


def get_file_tree(include_pattern: str | None = None, max_depth: int | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True
        )
        files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        logger.warning("git ls-files falhou, usando Path.glob como fallback")
        files = [str(p) for p in Path(".").rglob("*") if p.is_file()
                 and not any(part in EXCLUDE_DIRS for part in p.parts)
                 and p.suffix not in EXCLUDE_EXTS]

    if include_pattern:
        import fnmatch
        files = [f for f in files if fnmatch.fnmatch(f, include_pattern)]

    tree = defaultdict(list)
    for f in sorted(files):
        parts = f.split("/")
        if max_depth is not None and len(parts) > max_depth:
            parts = parts[:max_depth] + ["..."]
        tree[parts[0]].append("/".join(parts[1:]) if len(parts) > 1 else "")

    lines = []
    for root, children in sorted(tree.items()):
        lines.append(f"├── {root}/ ({len(children)} files)")
    return "\n".join(lines)


def extract_signatures(file_path: str) -> list[str]:
    ext = Path(file_path).suffix
    signatures = []

    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    patterns = {
        ".py": [
            (r"^(?:async\s+)?def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*\S+)?\s*:", "def"),
            (r"^class\s+(\w+)\s*(?:\((.*?)\))?\s*:", "class"),
        ],
        ".ts": [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*\S+)?\s*\{", "function"),
            (r"(?:export\s+)?class\s+(\w+)\s*(?:extends\s+\S+)?\s*\{", "class"),
            (r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)(?:\s*:\s*\S+)?\s*=>", "arrow"),
        ],
        ".js": [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)\s*\{", "function"),
            (r"(?:export\s+)?class\s+(\w+)\s*(?:extends\s+\S+)?\s*\{", "class"),
            (r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>", "arrow"),
        ],
        ".tsx": [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*\S+)?\s*\{", "function"),
            (r"(?:export\s+)?class\s+(\w+)\s*(?:extends\s+\S+)?\s*\{", "class"),
            (r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:\(.*?\)|React\.\w+)", "component"),
        ],
        ".go": [
            (r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\((.*?)\)(?:\s*\(.*?\)|\s+\S+)?\s*\{", "func"),
            (r"^type\s+(\w+)\s+struct\s*\{", "struct"),
        ],
        ".rs": [
            (r"^(?:pub\s+)?fn\s+(\w+)\s*\((.*?)\)(?:\s*->\s*\S+)?\s*\{", "fn"),
            (r"^(?:pub\s+)?struct\s+(\w+)\s*\{", "struct"),
        ],
        ".java": [
            (r"(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\((.*?)\)\s*\{", "method"),
            (r"(?:public\s+)?class\s+(\w+)", "class"),
        ],
    }

    patterns_for_file = patterns.get(ext, [])
    for pattern, kind in patterns_for_file:
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            params = match.group(2).strip() if match.lastindex >= 2 else ""
            if len(params) > 80:
                params = params[:77] + "..."
            signatures.append(f"  {kind} {name}({params})")

    return signatures


def extract_imports(file_path: str) -> list[str]:
    ext = Path(file_path).suffix
    imports = []

    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    patterns = {
        ".py": [r"^(?:from\s+(\S+)\s+)?import\s+(.+)$"],
        ".ts": [r"^import\s+.+\s+from\s+['\"]([^'\"]+)['\"]"],
        ".js": [r"^import\s+.+\s+from\s+['\"]([^'\"]+)['\"]"],
        ".tsx": [r"^import\s+.+\s+from\s+['\"]([^'\"]+)['\"]"],
        ".go": [r"^import\s+\"([^\"]+)\""],
    }

    patterns_for_file = patterns.get(ext, [])
    for pattern in patterns_for_file:
        for match in re.finditer(pattern, content, re.MULTILINE):
            imports.append(match.group(0).strip())

    return imports


def get_key_files(include_pattern: str | None = None, max_files: int = 50) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, check=True
        )
        files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        files = [str(p) for p in Path(".").rglob("*") if p.is_file()]

    code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb"}
    files = [f for f in files
             if Path(f).suffix in code_exts
             and not any(part in EXCLUDE_DIRS for part in Path(f).parts)
             and Path(f).suffix not in EXCLUDE_EXTS]

    if include_pattern:
        import fnmatch
        files = [f for f in files if fnmatch.fnmatch(f, include_pattern)]

    return sorted(files)[:max_files]


def build_map(include_pattern: str | None = None, max_depth: int | None = None,
              signatures_only: bool = False, max_files: int = 50) -> dict:

    file_tree = get_file_tree(include_pattern, max_depth)

    if signatures_only:
        file_tree = ""

    key_files = get_key_files(include_pattern, max_files)
    logger.info(f"📂 Analisando {len(key_files)} arquivos para assinaturas...")

    file_signatures = {}
    file_imports = {}

    for file_path in key_files:
        sigs = extract_signatures(file_path)
        if sigs:
            file_signatures[file_path] = sigs

        imps = extract_imports(file_path)
        if imps:
            file_imports[file_path] = imps[:10]

    total_signatures = sum(len(v) for v in file_signatures.values())
    total_imports = sum(len(v) for v in file_imports.values())
    logger.info(f"✅ {total_signatures} assinaturas, {total_imports} imports em {len(key_files)} arquivos")

    return {
        "file_tree": file_tree,
        "total_code_files": len(key_files),
        "files_with_signatures": len(file_signatures),
        "total_signatures": total_signatures,
        "total_imports": total_imports,
        "signatures": file_signatures,
        "imports": file_imports,
        "note": "Use --include 'src/**.ts' para filtrar. --max-depth N para limitar profundidade da árvore.",
    }


def format_map(result: dict) -> str:
    lines = []
    lines.append("## Estrutura do Projeto\n")
    lines.append("### Árvore de Arquivos\n")
    lines.append("```")
    lines.append(result["file_tree"])
    lines.append("```\n")

    lines.append(f"### Assinaturas ({result['total_signatures']} em {result['files_with_signatures']} arquivos)\n")

    for file_path in sorted(result["signatures"].keys()):
        lines.append(f"**{file_path}**")
        for sig in result["signatures"][file_path]:
            lines.append(sig)
        lines.append("")

    if result["imports"]:
        lines.append(f"### Dependências ({result['total_imports']} imports)\n")
        for file_path in sorted(result["imports"].keys())[:20]:
            lines.append(f"**{file_path}**")
            for imp in result["imports"][file_path][:5]:
                lines.append(f"  {imp}")
            if len(result["imports"][file_path]) > 5:
                lines.append(f"  ... +{len(result['imports'][file_path]) - 5} mais")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Gera índice estrutural do codebase para grounding do agente")
    parser.add_argument("--include", type=str, default=None,
                        help="Glob pattern para filtrar arquivos (ex: 'src/**.ts')")
    parser.add_argument("--max-depth", type=int, default=None,
                        help="Profundidade máxima da árvore de diretórios")
    parser.add_argument("--max-files", type=int, default=50,
                        help="Máximo de arquivos a analisar para assinaturas (default: 50)")
    parser.add_argument("--signatures-only", action="store_true",
                        help="Apenas assinaturas, sem árvore de diretórios")
    parser.add_argument("--json", action="store_true", help="Output em JSON para tool calls")
    args = parser.parse_args()

    result = build_map(
        include_pattern=args.include,
        max_depth=args.max_depth,
        signatures_only=args.signatures_only,
        max_files=args.max_files,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        try:
            print(format_map(result))
        except UnicodeEncodeError:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            print(format_map(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
