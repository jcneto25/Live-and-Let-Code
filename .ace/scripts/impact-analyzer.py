#!/usr/bin/env python3
"""
Analisa o impacto de alterações detectadas via git diff e reporta quais
artefatos LLC precisam ser revisados/atualizados em cascata.

Usa o grafo de dependências em .ace/dependency-graph.yaml.
Pode ser executado manualmente, via pre-commit hook, ou como tool call do agente.

Uso:
    python .ace/scripts/impact-analyzer.py
    python .ace/scripts/impact-analyzer.py --staged
    python .ace/scripts/impact-analyzer.py --files "docs/business/specs/glossario.md,src/auth/jwt.ts"
    python .ace/scripts/impact-analyzer.py --json
"""

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

GRAPH_FILE = Path(".ace/dependency-graph.yaml")


def load_graph() -> dict:
    if not GRAPH_FILE.exists():
        print(json.dumps({"error": f"{GRAPH_FILE} não encontrado"}), file=sys.stderr)
        sys.exit(1)
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_changed_files(staged: bool = False, files: str = None) -> list[str]:
    if files:
        return [f.strip() for f in files.split(",") if f.strip()]

    cmd = ["git", "diff", "--name-only"]
    if staged:
        cmd.append("--staged")
    if not staged:
        cmd.append("HEAD")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        return []


def match_artifact(changed_file: str, artifact: dict) -> bool:
    if "path" in artifact:
        return changed_file == artifact["path"]
    if "path_pattern" in artifact:
        return fnmatch.fnmatch(changed_file, artifact["path_pattern"])
    return False


def resolve_impact(artifact_ids: set, graph: dict, visited: set = None) -> list[dict]:
    """Propaga impacto em cascata através dos triggers_update."""
    if visited is None:
        visited = set()

    artifacts = graph.get("artifacts", {})
    impact = []

    for artifact_id in artifact_ids:
        if artifact_id in visited:
            continue
        visited.add(artifact_id)

        artifact = artifacts.get(artifact_id, {})
        triggers = artifact.get("triggers_update", [])

        for triggered_id in triggers:
            if triggered_id in artifacts:
                triggered = artifacts[triggered_id]
                impact.append({
                    "id": triggered_id,
                    "path": triggered.get("path", triggered.get("path_pattern", "")),
                    "triggered_by": artifact_id,
                    "depth": len(visited)
                })

        if triggers:
            sub_impact = resolve_impact(set(triggers), graph, visited)
            impact.extend(sub_impact)

    return impact


def build_report(changed_files: list[str], graph: dict) -> dict:
    artifacts = graph.get("artifacts", {})

    directly_affected = []
    for changed_file in changed_files:
        for artifact_id, artifact in artifacts.items():
            if match_artifact(changed_file, artifact):
                directly_affected.append({"file": changed_file, "artifact_id": artifact_id, "artifact_path": artifact.get("path", artifact.get("path_pattern", ""))})

    all_impact = resolve_impact(set(a["artifact_id"] for a in directly_affected), graph)

    deduped = []
    seen_paths = set()
    for item in all_impact:
        if item["path"] not in seen_paths and item["path"] not in {a["file"] for a in directly_affected}:
            seen_paths.add(item["path"])
            deduped.append(item)

    return {
        "changed_files": changed_files,
        "directly_affected": directly_affected,
        "cascade_impact": deduped,
        "total_artifacts_to_review": len(directly_affected) + len(deduped)
    }


def main():
    parser = argparse.ArgumentParser(description="Analisa impacto de alterações nos artefatos LLC")
    parser.add_argument("--staged", action="store_true", help="Analisa apenas arquivos staged")
    parser.add_argument("--files", type=str, help="Lista de arquivos separados por vírgula (ignora git diff)")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--skills", action="store_true", help="Sugere skills LLC a re-executar")
    args = parser.parse_args()

    graph = load_graph()
    changed_files = get_changed_files(staged=args.staged, files=args.files)

    if not changed_files:
        result = {"changed_files": [], "directly_affected": [], "cascade_impact": [], "total_artifacts_to_review": 0}
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("✅ Nenhuma alteração detectada.")
        return 0

    report = build_report(changed_files, graph)

    if args.json:
        output = dict(report)
        if args.skills:
            skills = set()
            for item in report["cascade_impact"]:
                for step_name, step_num in {"visao_estrategica": 0.5, "glossario": 1, "requisitos_funcionais": 1,
                    "requisitos_nao_funcionais": 1, "regras_negocio": 1, "workflows_bpmn": 1,
                    "perfis_permissoes": 1, "catalogo_integracoes": 1, "module_specs": 0.5,
                    "prd_executivo": 2, "prd_tecnico": 2, "prps": 3, "dependency_matrix": 4,
                    "plan": 4, "execution_waves": 4, "architecture": 5, "tasks": 6,
                    "design_system": 7, "mock_data": 8, "test_guide": 9,
                    "coverage_baseline": 9, "coverage_progress": 9, "readme": 10, "deployment": 10}.items():
                    if step_name in item.get("id", ""):
                        skills.add(f"llc-step-{step_num}")
            if skills:
                output["suggested_skills"] = sorted(skills, key=lambda s: float(s.replace("llc-step-", "")))
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"📊 ANÁLISE DE IMPACTO")
        print(f"{'='*60}")
        print(f"Arquivos alterados: {len(changed_files)}")
        for f in changed_files:
            print(f"   📄 {f}")

        if report["directly_affected"]:
            print(f"\n🎯 Artefatos DIRETAMENTE afetados ({len(report['directly_affected'])}):")
            for a in report["directly_affected"]:
                print(f"   📝 {a['artifact_id']} → {a.get('artifact_path', '?')}")

        if report["cascade_impact"]:
            print(f"\n🔗 Impacto em CASCATA — revisar nesta ordem ({len(report['cascade_impact'])}):")
            for i, item in enumerate(report["cascade_impact"], 1):
                print(f"   {i}. {item['id']} → {item['path']} (disparado por: {item['triggered_by']})")

        if args.skills and report["cascade_impact"]:
            skills = set()
            step_map = {"visao_estrategica": 0.5, "glossario": 1, "requisitos_funcionais": 1,
                "requisitos_nao_funcionais": 1, "regras_negocio": 1, "workflows_bpmn": 1,
                "perfis_permissoes": 1, "catalogo_integracoes": 1, "module_specs": 0.5,
                "prd_executivo": 2, "prd_tecnico": 2, "prps": 3, "dependency_matrix": 4,
                "plan": 4, "execution_waves": 4, "architecture": 5, "tasks": 6,
                "design_system": 7, "mock_data": 8, "test_guide": 9,
                "coverage_baseline": 9, "coverage_progress": 9, "readme": 10, "deployment": 10}
            for item in report["cascade_impact"]:
                for name, num in step_map.items():
                    if name in item.get("id", ""):
                        skills.add(f"llc-step-{num}")
            if skills:
                print(f"\n💡 Skills sugeridas para re-execução:")
                for s in sorted(skills, key=lambda x: float(x.replace("llc-step-", ""))):
                    print(f"   → {s}")

        if report["total_artifacts_to_review"] == 0:
            print(f"\n✅ Nenhum artefato LLC afetado pelas alterações.")
        else:
            print(f"\n📋 Total de artefatos a revisar: {report['total_artifacts_to_review']}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
