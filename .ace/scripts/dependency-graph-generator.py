#!/usr/bin/env python3
"""
dependency-graph-generator — Gerador de dependency-graph.yaml baseado em PRPs.

Uso:
    python .ace/scripts/dependency-graph-generator.py --prps docs/prps/PRP-001.md docs/prps/PRP-002.md
    python .ace/scripts/dependency-graph-generator.py --output .ace/dependency-graph.yaml
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

PRP_PATTERN = re.compile(r"PRP-(\d{3})")


def extract_prp_dependencies(prp_content: str) -> list[str]:
    """Extrai dependências de um PRP (referências a outros PRPs no texto)."""
    deps = set()
    for match in PRP_PATTERN.finditer(prp_content):
        deps.add(f"PRP-{match.group(1)}")
    return sorted(deps)


def generate_dependency_graph(prp_files: list[Path]) -> dict:
    """Gera o grafo de dependências baseado nos PRPs."""
    prps = {}

    for prp_file in prp_files:
        content = prp_file.read_text(encoding="utf-8")
        match = PRP_PATTERN.search(content)
        if match:
            prp_id = f"PRP-{match.group(1)}"
            prps[prp_id] = {
                "path": str(prp_file),
                "dependencies": extract_prp_dependencies(content),
            }

    # Constrói o grafo
    graph = {
        "version": "1.2.0",
        "generated_by": "dependency-graph-generator",
        "last_updated": "2026-07-04",
        "artifacts": {},
    }

    # PRPs
    for prp_id, info in prps.items():
        triggers = []
        for other_prp_id, other_info in prps.items():
            if prp_id in other_info["dependencies"]:
                triggers.append(other_prp_id)

        graph["artifacts"][prp_id.lower().replace("-", "_")] = {
            "path_pattern": f"docs/prps/{prp_id}-*.md",
            "depends_on": info["dependencies"],
            "triggers_update": triggers,
        }

    # artefatos de planejamento
    graph["artifacts"]["dependency_matrix"] = {
        "path": "docs/planning/DEPENDENCY_MATRIX.md",
        "depends_on": list(prps.keys()),
        "triggers_update": ["execution_waves", "plan"],
    }

    graph["artifacts"]["execution_waves"] = {
        "path": "docs/planning/EXECUTION_WAVES.md",
        "depends_on": list(prps.keys()),
        "triggers_update": [],
    }

    return graph


def yaml_dump(data: dict, indent: int = 0) -> str:
    """Serializa dict para YAML simples (sem dependências externas)."""
    result = []
    prefix = "  " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                result.append(f"{prefix}{key}:")
                result.append(yaml_dump(value, indent + 1))
            else:
                if isinstance(value, str):
                    result.append(
                        f'{prefix}- "{value}"'
                        if indent > 0
                        else f"{prefix}{key}: {value}"
                    )
                elif isinstance(value, list):
                    result.append(f"{prefix}{key}:")
                    for item in value:
                        result.append(f"{prefix}  - {item}")
                else:
                    result.append(f"{prefix}{key}: {value}")

    return "\n".join(result)


def main():
    parser = argparse.ArgumentParser(
        description="Gerador de dependency-graph.yaml baseado em PRPs"
    )
    parser.add_argument(
        "--prps", nargs="+", type=Path, help="Arquivos PRP para analisar"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(".ace/dependency-graph.yaml"),
        help="Arquivo de saída",
    )
    args = parser.parse_args()

    if not args.prps:
        print("ERROR: Especifique pelo menos um arquivo PRP com --prps")
        sys.exit(1)

    for prp_file in args.prps:
        if not prp_file.exists():
            print(f"ERROR: PRP não encontrado: {prp_file}")
            sys.exit(1)

    graph = generate_dependency_graph(args.prps)
    yaml_content = yaml_dump(graph)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml_content, encoding="utf-8")

    print(f"✅ dependency-graph.yaml gerado em: {args.output}")


if __name__ == "__main__":
    main()
