#!/usr/bin/env python3
"""initialize_session — grafo de dependências e contexto derivado."""

import hashlib
import json
from typing import Optional

from .paths import GRAPH_FILE, STEP_ARTIFACTS, logger

try:
    import yaml
except ImportError:
    yaml = None


def load_dependency_graph() -> Optional[dict]:
    """Carrega o grafo de dependências do .ace/dependency-graph.yaml."""
    if not GRAPH_FILE.exists():
        return None
    if yaml is None:
        logger.warning("⚠️  PyYAML não instalado — não foi possível carregar o grafo de dependências.")
        return None
    try:
        return yaml.safe_load(GRAPH_FILE.read_text(encoding='utf-8'))
    except (yaml.YAMLError, OSError) as e:
        logger.warning(f"⚠️  Erro ao ler {GRAPH_FILE}: {e}")
        return None


def resolve_triggers(artifact_ids: list[str], graph: dict, max_depth: int = 2) -> list[dict]:
    """Propaga triggers_update em cascata a partir dos artefatos fornecidos.

    Retorna lista de {id, path, triggered_by, depth} até max_depth.
    """
    artifacts = graph.get("artifacts", {})
    result: list[dict] = []
    visited: set[str] = set()
    queue: list[tuple[str, str, int]] = [(aid, "(step)", 0) for aid in artifact_ids]

    while queue:
        artifact_id, triggered_by, depth = queue.pop(0)
        if artifact_id in visited or depth > max_depth:
            continue
        visited.add(artifact_id)

        artifact = artifacts.get(artifact_id, {})
        path = artifact.get("path") or artifact.get("path_pattern", "")
        if depth > 0:
            result.append({
                "id": artifact_id,
                "path": path,
                "triggered_by": triggered_by,
                "depth": depth,
            })

        for trigger_id in artifact.get("triggers_update", []):
            if trigger_id not in visited:
                queue.append((trigger_id, artifact_id, depth + 1))

    return result


def build_dependency_context(step_number: float, graph: Optional[dict]) -> str:
    """Constrói o bloco de dependências com checksum e métricas."""
    if not graph:
        return ""

    primary = STEP_ARTIFACTS.get(step_number, [])
    if not primary:
        return ""

    cascade = resolve_triggers(primary, graph)
    n_artifacts = len(primary)
    n_triggers = len(cascade)

    lines = [f"checksum: sha256:{compute_checksum(cascade)}"]
    lines.append(f"artifacts: {n_artifacts}")
    lines.append(f"triggers: {n_triggers}")
    lines.append("list:")

    for dep in cascade:
        artifact = graph.get("artifacts", {}).get(dep["id"], {})
        path = artifact.get("path") or artifact.get("path_pattern", "")
        lines.append(f"  - artifact: {dep['id']}")
        lines.append(f"    path: {path}")
        lines.append(f"    reason: triggered_by {dep['triggered_by']} (depth {dep['depth']})")

    result = "\n".join(lines)

    char_count = len(result)
    token_estimate = char_count // 4
    logger.info(f"📊 Subgrafo: {n_artifacts} artefatos, {n_triggers} triggers, "
                f"{char_count} chars (~{token_estimate} tokens)")

    return result


def compute_checksum(data: list) -> str:
    """SHA256 checksum de uma lista de dicts (serializada como JSON estável)."""
    if hashlib is None:
        return "unavailable"
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:16]
