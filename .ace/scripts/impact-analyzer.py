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
    python .ace/scripts/impact-analyzer.py --classify       # major/minor classification
    python .ace/scripts/impact-analyzer.py --reverse         # backward traversal (depends_on)
    python .ace/scripts/impact-analyzer.py --reverse --files "src/auth/jwt.ts"
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

import yaml

GRAPH_FILE = Path(".ace/dependency-graph.yaml")

SOURCE_PATTERNS = {
    "src": "src/**/*",
    "test": "**/*.test.*",
    "spec": "**/*.spec.*",
    "migration": "**/prisma/migrations/**/*",
    "config_infra": "**/{Dockerfile,docker-compose*.yml,.github/**/*,.gitlab-ci.yml,nginx.conf,.env.example,tsconfig.json}",
    "schema": "**/prisma/schema.prisma",
    "e2e": "**/*.e2e-spec.*",
    "mock": "mocks/**/*",
}

MAJOR_THRESHOLDS = {
    "architecture": "architecture",
    "design_system": "design_system",
    "perfis_permissoes": "perfis_permissoes",
    "schema": "schema",
    "migration": "migration",
}

PRP_COUNT_MAJOR_THRESHOLD = 3


def _skill_num(slug: str) -> float:
    try:
        return float(slug.replace("llc-step-", ""))
    except ValueError:
        return 9999.0


def load_graph() -> dict:
    if not GRAPH_FILE.exists():
        print(json.dumps({"error": f"{GRAPH_FILE} nao encontrado"}), file=sys.stderr)
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


def classify_source_file(changed_file: str) -> str | None:
    for category, pattern in SOURCE_PATTERNS.items():
        if fnmatch.fnmatch(changed_file, pattern):
            return category
    return None


def resolve_impact(artifact_ids: set, graph: dict, visited: set = None) -> list[dict]:
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
                path = triggered.get("path", triggered.get("path_pattern", ""))
                if path not in {p["path"] for p in impact}:
                    impact.append({
                        "id": triggered_id,
                        "path": path,
                        "triggered_by": artifact_id,
                        "depth": len(visited),
                    })

        if triggers:
            sub_impact = resolve_impact(set(triggers), graph, visited)
            impact.extend(sub_impact)

    return impact


def resolve_depends(artifact_ids: set, graph: dict, visited: set = None) -> list[dict]:
    if visited is None:
        visited = set()

    artifacts = graph.get("artifacts", {})
    impact = []

    for artifact_id in artifact_ids:
        if artifact_id in visited:
            continue
        visited.add(artifact_id)

        for other_id, other in artifacts.items():
            deps = other.get("depends_on", [])
            if artifact_id in deps and other_id not in visited:
                path = other.get("path", other.get("path_pattern", ""))
                impact.append({
                    "id": other_id,
                    "path": path,
                    "depends_on": artifact_id,
                    "depth": len(visited),
                })
                sub_impact = resolve_depends({other_id}, graph, visited)
                impact.extend(sub_impact)

    return impact


def classify_change(directly_affected: list[dict], cascade_impact: list[dict],
                    changed_files: list[str]) -> dict:
    reasons = []
    affected_ids = {a["artifact_id"] for a in directly_affected}
    cascade_ids = {c["id"] for c in cascade_impact}
    all_ids = affected_ids | cascade_ids

    for threshold_id in MAJOR_THRESHOLDS:
        if threshold_id in all_ids:
            reasons.append(f"Afeta {threshold_id}")
        for f in changed_files:
            category = classify_source_file(f)
            if category == threshold_id:
                reasons.append(f"Arquivo de {threshold_id} modificado: {f}")

    for f in changed_files:
        cat = classify_source_file(f)
        if cat in ("migration", "schema"):
            reasons.append(f"Migration/schema alterado: {f}")
        elif cat == "config_infra":
            reasons.append(f"Config de infraestrutura alterada: {f}")

    prp_ids = {aid for aid in all_ids if "prp" in aid.lower()}
    prp_count = len(prp_ids)
    if prp_count >= PRP_COUNT_MAJOR_THRESHOLD:
        reasons.append(f"{prp_count} PRPs afetados (threshold: {PRP_COUNT_MAJOR_THRESHOLD})")

    is_major = len(reasons) > 0

    return {
        "change_type": "major" if is_major else "minor",
        "trigger_reasons": reasons if is_major else [],
        "affected_prp_count": prp_count,
    }


def build_report(changed_files: list[str], graph: dict,
                 reverse: bool = False) -> dict:
    artifacts = graph.get("artifacts", {})

    directly_affected = []
    matched_artifact_ids = set()

    for changed_file in changed_files:
        for artifact_id, artifact in artifacts.items():
            if match_artifact(changed_file, artifact):
                directly_affected.append({
                    "file": changed_file,
                    "artifact_id": artifact_id,
                    "artifact_path": artifact.get("path", artifact.get("path_pattern", "")),
                })
                matched_artifact_ids.add(artifact_id)

    unmatched = [f for f in changed_files
                 if not any(match_artifact(f, a) for a in artifacts.values())]
    source_categories = {}
    for f in unmatched:
        cat = classify_source_file(f)
        if cat:
            source_categories.setdefault(cat, []).append(f)

    if reverse and matched_artifact_ids:
        all_impact = resolve_depends(matched_artifact_ids, graph)
    else:
        all_impact = resolve_impact(matched_artifact_ids, graph)

    deduped = []
    seen_paths = set()
    for item in all_impact:
        path = item["path"]
        if path and path not in seen_paths and path not in {a["file"] for a in directly_affected}:
            seen_paths.add(path)
            deduped.append(item)

    return {
        "changed_files": changed_files,
        "directly_affected": directly_affected,
        "cascade_impact": deduped,
        "total_artifacts_to_review": len(directly_affected) + len(deduped),
        "unmatched_source": source_categories if source_categories else {},
    }


def format_output(report: dict, args: argparse.Namespace, step_map: dict) -> dict:
    output = dict(report)

    if args.classify:
        classification = classify_change(
            report["directly_affected"],
            report["cascade_impact"],
            report["changed_files"],
        )
        output["classification"] = classification

    if args.skills:
        skills = set()
        for item in report["cascade_impact"]:
            for name, num in step_map.items():
                if name in item.get("id", ""):
                    skills.add(f"llc-step-{num}")
        output["suggested_skills"] = sorted(skills, key=_skill_num) if skills else []

    if args.reverse:
        output["direction"] = "reverse"
        output["direction_description"] = (
            "Analise reversa: artefatos que DEPENDEM dos arquivos alterados. "
            "Estes precisam ser revisados porque dependem do que mudou."
        )
    else:
        output["direction"] = "forward"
        output["direction_description"] = (
            "Analise direta: artefatos IMPACTADOS pelos arquivos alterados. "
            "Estes precisam ser atualizados por causa da mudanca."
        )

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Analisa impacto de alteracoes nos artefatos LLC")
    parser.add_argument("--staged", action="store_true",
                        help="Analisa apenas arquivos staged")
    parser.add_argument("--files", type=str,
                        help="Lista de arquivos separados por virgula (ignora git diff)")
    parser.add_argument("--json", action="store_true",
                        help="Output em JSON")
    parser.add_argument("--skills", action="store_true",
                        help="Sugere skills LLC a re-executar")
    parser.add_argument("--reverse", action="store_true",
                        help="Analise reversa: artefatos que DEPENDEM dos alterados")
    parser.add_argument("--classify", action="store_true",
                        help="Classifica mudanca como MAJOR ou MINOR")
    args = parser.parse_args()

    step_map = {
        "delta_report": 0,
        "visao_estrategica": 0.5,
        "glossario": 1, "requisitos_funcionais": 1,
        "requisitos_nao_funcionais": 1, "regras_negocio": 1,
        "workflows_bpmn": 1, "perfis_permissoes": 1,
        "catalogo_integracoes": 1, "module_specs": 0.5,
        "prd_executivo": 2, "prd_tecnico": 2,
        "prps": 3, "dependency_matrix": 4,
        "plan": 4, "execution_waves": 4,
        "architecture": 5, "tasks": 6,
        "design_system": 7, "mock_data": 8,
        "test_guide": 9, "coverage_baseline": 9,
        "coverage_progress": 9, "readme": 10,
        "deployment": 10, "user_guide_skeleton": 10.5,
        "security_audit_report": 10.6, "null_safety_report": 10.7,
        "owasp_hardening_report": 11.1,
    }

    graph = load_graph()
    changed_files = get_changed_files(staged=args.staged, files=args.files)

    if not changed_files:
        result = {
            "changed_files": [],
            "directly_affected": [],
            "cascade_impact": [],
            "unmatched_source": {},
            "total_artifacts_to_review": 0,
        }
        if args.classify:
            result["classification"] = {
                "change_type": "none",
                "trigger_reasons": [],
                "affected_prp_count": 0,
            }
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Nenhuma alteracao detectada.")
        return 0

    report = build_report(changed_files, graph, reverse=args.reverse)
    output = format_output(report, args, step_map)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    # Human-readable output
    print(f"\n{'='*60}")
    print(f" ANALISE DE IMPACTO")
    if args.reverse:
        print(f"   Modo REVERSO — artefatos que dependem das alteracoes")
    else:
        print(f"   Modo DIRETO — artefatos impactados pelas alteracoes")
    print(f"{'='*60}")

    if "classification" in output:
        cls = output["classification"]
        icon = " MAJOR" if cls["change_type"] == "major" else " MINOR"
        print(f"\nClassificacao: {icon}")
        if cls["trigger_reasons"]:
            for r in cls["trigger_reasons"]:
                print(f"   -> {r}")
        if cls["affected_prp_count"] > 0:
            print(f"   PRPs afetados: {cls['affected_prp_count']}")

    print(f"\nArquivos alterados ({len(changed_files)}):")
    for f in changed_files:
        cat = classify_source_file(f)
        tag = f" [{cat}]" if cat else ""
        print(f"   {f}{tag}")

    if output["directly_affected"]:
        print(f"\nArtefatos DIRETAMENTE afetados ({len(output['directly_affected'])}):")
        for a in output["directly_affected"]:
            print(f"   {a['artifact_id']} -> {a.get('artifact_path', '?')}")

    if output["cascade_impact"]:
        label = "REVERSO — Dependem de" if args.reverse else "CASCATA — revisar nesta ordem"
        print(f"\n{label} ({len(output['cascade_impact'])}):")
        for i, item in enumerate(output["cascade_impact"], 1):
            triggered_by = item.get("triggered_by", item.get("depends_on", "?"))
            print(f"   {i}. {item['id']} -> {item['path']} (via: {triggered_by})")

    if output.get("unmatched_source"):
        print(f"\nArquivos de codigo-fonte (sem mapeamento no YAML):")
        for cat, files in output["unmatched_source"].items():
            print(f"   [{cat}]: {', '.join(files)}")

    if output.get("suggested_skills"):
        print(f"\nSkills sugeridas para re-execucao:")
        for s in output["suggested_skills"]:
            print(f"   -> {s}")

    if output["total_artifacts_to_review"] == 0 and not output.get("unmatched_source"):
        print(f"\nNenhum artefato LLC afetado pelas alteracoes.")
    else:
        print(f"\nTotal de artefatos a revisar: {output['total_artifacts_to_review']}")
        if output.get("unmatched_source"):
            print(f"Arquivos de codigo sem mapeamento: {sum(len(v) for v in output['unmatched_source'].values())}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
