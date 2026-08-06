"""llc_graph.model — modelo de nós e arestas do grafo do pipeline LLC.

ADR-0004 §2.3. Todo nó/aresta é imutável (frozen dataclass — RF-G1A.1).
Python puro (D6): dataclasses + adjacência, sem networkx.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeKind(str, Enum):
    """Tipos de nó do grafo (ADR-0004 §2.3)."""

    STEP = "step"      # unidade do pipeline macro
    PRP = "prp"        # unidade paralelizável de execução
    GATE = "gate"      # decisão humana (ESPECIAL)
    HITL = "hitl"      # pergunta/review durante execução


class NodeState(str, Enum):
    """Estados possíveis de um nó (ADR-0004 §2.3)."""

    PENDING = "pending"
    READY = "ready"                     # deps satisfeitas, elegível
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"   # gate/hitl parado p/ humano
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class EdgeKind(str, Enum):
    """Tipos de aresta do grafo (ADR-0004 §2.3)."""

    DEPENDS_ON = "depends_on"   # aresta de controle
    PRODUCES = "produces"       # aresta de data-flow (artefato)
    BLOCKS = "blocks"           # gate bloqueia sucessores até aprovação
    REWORK = "rework"           # liga instância original à retry


@dataclass(frozen=True)
class GraphNode:
    """Nó imutável do grafo (RF-G1A.1)."""

    id: str                        # "step-5" | "prp-004" | "gate-5" | "hitl-q123"
    kind: NodeKind
    requires_human: bool           # True para GATE e HITL
    auto_parallelizable: bool      # True para PRP; False p/ step com gate
    depends_on: tuple[str, ...] = ()    # arestas de entrada (imutável)
    produces: tuple[str, ...] = ()      # artefatos gerados
    retry_of: str | None = None         # aponta p/ instância original se rework


@dataclass(frozen=True)
class GraphEdge:
    """Aresta imutável do grafo (DoD — frozen)."""

    source: str
    target: str
    kind: EdgeKind


@dataclass
class Graph:
    """Grafo dirigido com adjacência (D6 — dataclasses + adjacência)."""

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)

    def node(self, node_id: str) -> GraphNode | None:
        return self.nodes.get(node_id)

    def successors(self, node_id: str) -> list[str]:
        return [e.target for e in self.edges if e.source == node_id]

    def predecessors(self, node_id: str) -> list[str]:
        return [e.source for e in self.edges if e.target == node_id]

    @property
    def nodes_count(self) -> int:
        return len(self.nodes)
