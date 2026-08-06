"""llc_graph.builder — GraphBuilder: estrutura declarada do grafo.

ADR-0004 D2: unifica a ordem sequencial do REGISTRY (StepSpec.number — N1),
gates.json (nós de gate) e dependency-graph.yaml (N2 — PRPs/artefatos).
Zero mudança no harness. DIP: importa apenas llc_steps (fonte declarativa).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import yaml

from llc_steps import REGISTRY, normalize_step

from llc_graph.model import EdgeKind, Graph, GraphEdge, GraphNode, NodeKind


class GraphBuilder:
    """Constrói o DAG do pipeline a partir das fontes declarativas.

    Injetável para testes: registry, gates_path e yaml_path podem ser
    substituídos; por padrão lê do repositório real.
    """

    def __init__(
        self,
        project_root: Path | str | None = None,
        registry: dict | None = None,
        gates_path: Path | str | None = None,
        yaml_path: Path | str | None = None,
    ):
        self.root = Path(project_root) if project_root else Path(".")
        self.registry = registry if registry is not None else REGISTRY
        self._gates_path = (
            Path(gates_path) if gates_path else self.root / ".ace" / "config" / "gates.json"
        )
        self._yaml_path = (
            Path(yaml_path) if yaml_path else self.root / ".ace" / "dependency-graph.yaml"
        )

    def build(self) -> Graph:
        """Constrói o grafo completo (N1 steps + gates + N2 artefatos)."""
        graph = Graph()
        self._add_step_nodes(graph)
        self._add_gate_nodes(graph)
        self._add_artifact_nodes(graph)
        self._warn_orphans(graph)
        return graph

    # ── N1: steps do REGISTRY (ordem sequencial) ────────────────────────────
    def _ordered_steps(self) -> list:
        """Steps in_pipeline ordenados por StepSpec.number (D2/RF-G1A.3)."""
        return sorted(
            (s for s in self.registry.values() if s.in_pipeline),
            key=lambda s: s.number,
        )

    def _add_step_nodes(self, graph: Graph) -> None:
        steps = self._ordered_steps()
        for i, spec in enumerate(steps):
            node_id = f"step-{spec.id}"
            graph.add_node(GraphNode(
                id=node_id,
                kind=NodeKind.STEP,
                requires_human=False,
                auto_parallelizable=spec.gate is None,  # step com gate não é auto-paralelizável
            ))
            if i > 0:
                graph.add_edge(GraphEdge(
                    source=f"step-{steps[i - 1].id}",
                    target=node_id,
                    kind=EdgeKind.DEPENDS_ON,
                ))

    # ── Gates: nós especiais (RF-G1A.2 / D3) ────────────────────────────────
    def _add_gate_nodes(self, graph: Graph) -> None:
        gates = self._load_gates()
        steps = self._ordered_steps()
        step_ids = [s.id for s in steps]
        for gate_id, gate_def in gates.items():
            node_id = f"gate-{gate_id}"
            graph.add_node(GraphNode(
                id=node_id,
                kind=NodeKind.GATE,
                requires_human=True,          # D3 — nunca auto-avançado
                auto_parallelizable=False,    # D3
            ))
            raw_step = gate_def.get("step") if isinstance(gate_def, dict) else None
            if raw_step is None:
                continue
            try:
                canonical = normalize_step(raw_step).id
            except Exception:  # noqa: BLE001 — step fora do REGISTRY não quebra o build
                canonical = str(raw_step)
            gated_step = f"step-{canonical}"
            graph.add_edge(GraphEdge(
                source=gated_step, target=node_id, kind=EdgeKind.DEPENDS_ON,
            ))
            # gate bloqueia o sucessor do step que gateia (ADR-0004 §2.4)
            if canonical in step_ids:
                idx = step_ids.index(canonical)
                if idx + 1 < len(step_ids):
                    graph.add_edge(GraphEdge(
                        source=node_id,
                        target=f"step-{step_ids[idx + 1]}",
                        kind=EdgeKind.BLOCKS,
                    ))

    # ── N2: artefatos do dependency-graph.yaml (RF-G1A.3) ───────────────────
    def _add_artifact_nodes(self, graph: Graph) -> None:
        artifacts = self._load_artifacts()
        for artifact_id, defn in artifacts.items():
            depends = defn.get("depends_on", []) if isinstance(defn, dict) else []
            produces = (
                defn.get("path") or defn.get("path_pattern") or ""
                if isinstance(defn, dict) else ""
            )
            graph.add_node(GraphNode(
                id=artifact_id,
                kind=NodeKind.PRP,
                requires_human=False,
                auto_parallelizable=True,  # N2 — unidade paralelizável
                produces=(produces,) if produces else (),
            ))
            for dep in depends:
                graph.add_edge(GraphEdge(
                    source=str(dep), target=artifact_id, kind=EdgeKind.DEPENDS_ON,
                ))

    # ── Órfãos (RF-G1A.4) ───────────────────────────────────────────────────
    def _warn_orphans(self, graph: Graph) -> None:
        """Warning para toda aresta que referencia nó inexistente."""
        for edge in graph.edges:
            if edge.source not in graph.nodes:
                warnings.warn(
                    f"Nó órfão: dependência {edge.source!r} (target={edge.target!r}) "
                    "não existe no grafo", UserWarning, stacklevel=2,
                )
            if edge.target not in graph.nodes:
                warnings.warn(
                    f"Nó órfão: target {edge.target!r} (source={edge.source!r}) "
                    "não existe no grafo", UserWarning, stacklevel=2,
                )

    # ── Rework (RF-G1A.7 / D4) ──────────────────────────────────────────────
    def add_rework_node(self, graph: Graph, original_id: str) -> GraphNode:
        """Cria nova instância imutável do nó ligada ao original por REWORK.

        DAG preservado: rework nunca muta o original nem cria ciclo.
        """
        original = graph.node(original_id)
        if original is None:
            raise KeyError(f"Nó original não encontrado: {original_id}")
        retries = [
            nid for nid in graph.nodes
            if nid.startswith(f"{original_id}-retry-")
        ]
        retry_id = f"{original_id}-retry-{len(retries) + 1}"
        retry = GraphNode(
            id=retry_id,
            kind=original.kind,
            requires_human=original.requires_human,
            auto_parallelizable=original.auto_parallelizable,
            depends_on=(original_id,),
            produces=original.produces,
            retry_of=original_id,
        )
        graph.add_node(retry)
        graph.add_edge(GraphEdge(source=original_id, target=retry_id, kind=EdgeKind.REWORK))
        return retry

    # ── Leitura de fontes (read-only, tolerante) ────────────────────────────
    def _load_gates(self) -> dict:
        if not self._gates_path.exists():
            return {}
        try:
            data = json.loads(self._gates_path.read_text(encoding="utf-8"))
            return data.get("gates", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_artifacts(self) -> dict:
        if not self._yaml_path.exists():
            return {}
        try:
            data = yaml.safe_load(self._yaml_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            return {}
        return (data or {}).get("artifacts", {}) or {}
