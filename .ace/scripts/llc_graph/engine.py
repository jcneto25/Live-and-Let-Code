"""llc_graph.engine — GraphEngine: scheduler read-only (ADR-0004 §2.7).

Responde "quais nós estão prontos para execução?" e "quais nós são
afetados por uma mudança?". É a fundação do Smart Skip formal e da futura
coordenação reativa. NUNCA escreve no disco — projeções são queries puras
(CQS); o estado continua sendo derivado das sessões ACE (D1/P3).

# Invariante do contrato (PRP-GRAPH-1B §3 — documentado em código)
# ready_nodes() decide ELEGIBILIDADE DE EXECUÇÃO (deps DAG satisfeitas).
# NÃO decide qualidade de merge — isso é Gate 10.8/11.3 (fitness functions).
# Os dois sistemas são camadas consecutivas, nunca alternativas.
# Um nó READY pode ainda falhar no gate de fitness — comportamento correto.
"""
from __future__ import annotations

import heapq
import json
import re
from datetime import datetime
from pathlib import Path

from llc_graph.model import (
    EdgeKind,
    Graph,
    GraphNode,
    NodeKind,
    NodeState,
)
from llc_graph.state import AceStateReader


class GraphEngine:
    """Scheduler read-only: deriva estado e elegibilidade do grafo + ACE."""

    def __init__(
        self,
        graph: Graph,
        state_reader: AceStateReader | None = None,
        project_root: Path | str | None = None,
    ):
        self.graph = graph
        self.root = Path(project_root) if project_root else Path(".")
        self.state_reader = state_reader or AceStateReader(project_root=self.root)
        self._sessions_dir = self.root / ".ace" / "sessions"

    # ── Estado derivado ────────────────────────────────────────────────────
    def node_state(self, node_id: str) -> NodeState:
        """Deriva o estado atual do nó (D1 — sempre a partir do ACE).

        Precedência: (1) estado real do ACE (DONE/FAILED/SKIPPED/RUNNING);
        (2) decisão de gate real (<gate_result> na sessão do step gateado);
        (3) deps satisfeitas → AWAITING_HUMAN (requires_human) ou READY;
        (4) senão PENDING.
        """
        node = self.graph.node(node_id)
        if node is None:
            raise KeyError(f"Nó não encontrado no grafo: {node_id}")
        base = self.state_reader.node_state(node_id)
        if base in (NodeState.DONE, NodeState.FAILED, NodeState.SKIPPED,
                    NodeState.RUNNING):
            # Paridade PipelineDataReader §7.6 (GOV-003/R4): step cuja sessão
            # completou mas o gate foi REJEITADO é FAILED (rework), não DONE.
            if node.kind == NodeKind.STEP and base is NodeState.DONE:
                gate = self._gate_for_step(node.id)
                if gate is not None and self._gate_decision(gate) == "rejected":
                    return NodeState.FAILED
            return base
        if node.kind == NodeKind.GATE:
            decision = self._gate_decision(node)
            if decision == "approved":
                return NodeState.DONE
            if decision == "rejected":
                return NodeState.FAILED
        if not self._deps_satisfied(node):
            return NodeState.PENDING
        if node.requires_human:
            # D3 — estaciona na fila do humano; única saída: UserDecisionWriter
            return NodeState.AWAITING_HUMAN
        return NodeState.READY

    def ready_nodes(self) -> list[GraphNode]:
        """Nós elegíveis: deps satisfeitas e estado READY ou AWAITING_HUMAN.

        - requires_human → AWAITING_HUMAN (fila do humano) — NUNCA auto-executado.
        - caso contrário → READY (elegível para agente/Herdr).
        Determinístico: ordem estável por id (RF-G1B.7).
        """
        ready = [
            n for n in self.graph.nodes.values()
            if self.node_state(n.id) in (NodeState.READY, NodeState.AWAITING_HUMAN)
        ]
        return sorted(ready, key=lambda n: n.id)

    def parallel_frontier(self) -> list[GraphNode]:
        """Nós elegíveis para execução simultânea (ADR-0004 §2.7, Q2).

        Retorna DADOS puros agnósticos de runtime (PRP-GRAPH-2A):
        - todos têm auto_parallelizable=True (RF-G2A.1)
        - nenhum par tem aresta entre si — mutuamente independentes (RF-G2A.2)
        - subconjunto de ready_nodes() (RF-G2A.3)
        - nenhum requires_human=True (RF-G2A.4)
        - determinístico e sem side-effects (CQS — RF-G2A.5)

        Este método NÃO executa nada, NÃO invoca runtime e NÃO sabe que
        Herdr, worktrees ou qualquer ferramenta existe (Q2). O consumidor
        decide o que fazer com a lista.

        Seleção gulosa determinística: itera os candidatos na ordem estável
        de ready_nodes() (por id) e inclui cada nó se não tiver aresta com
        nenhum já selecionado — garante independência mútua por construção.
        """
        candidates = [
            n for n in self.ready_nodes()
            if n.auto_parallelizable and not n.requires_human
        ]
        frontier: list[GraphNode] = []
        for node in candidates:
            if all(
                not self._has_edge_between(node.id, other.id)
                for other in frontier
            ):
                frontier.append(node)
        return frontier

    # Pesos do caminho crítico (PRP-GRAPH-2B §3 — estimativa determinística)
    _STEP_WEIGHT = 1.0       # uma unidade de trabalho
    _GATE_WEIGHT = 2.0       # espera humana (estimada; histórico ACE é futuro)
    _SKIPPED_WEIGHT = 0.0    # não contribui para a duração

    def critical_path(self) -> list[GraphNode]:
        """Caminho crítico do DAG — sequência que determina a duração total
        (ADR-0004 §2.7: responde 'onde está o gargalo?').

        Algoritmo: topological sort (Kahn) + relaxação de arestas — O(V+E),
        NUNCA O(V²) (PRP-GRAPH-2B §5). Pesos:
        - SKIPPED → 0 (não contribui para o comprimento)
        - GATE → 2.0 (tempo médio de espera humana, estimado)
        - demais → 1.0 (unidade de trabalho)

        Query pura (CQS): não muta grafo nem sessões; determinístico
        (ordenação estável por id e desempate por menor id).

        Retorna a lista de GraphNode do caminho, em ordem topológica
        (RF-G2B.1/2/3). Vazio se o grafo for vazio.
        """
        if not self.graph.nodes:
            return []
        topo = self._topological_order()
        # dist[v] = maior peso acumulado até v; prev[v] = nó anterior no caminho
        # dist[v] = peso acumulado do caminho que termina em v, SEM contar o
        # peso de v (adicionado quando v é processado no loop — cada peso
        # conta exatamente uma vez). prev[v] = nó anterior no caminho.
        dist: dict[str, float] = {nid: 0.0 for nid in topo}
        prev: dict[str, str | None] = {nid: None for nid in topo}
        for nid in topo:
            dist[nid] += self._path_weight(self.graph.nodes[nid])
            for succ in sorted(self.graph.successors(nid)):
                if succ not in dist:
                    continue
                # NÃO adicionar peso(succ) aqui — seria double-count (o peso
                # de succ entra quando succ é processado). cand = acumulado
                # até nid (que já inclui nid); o peso de succ soma depois.
                cand = dist[nid]
                # empate: mantém o predecessor de menor id (determinístico)
                if cand > dist[succ] or (
                    cand == dist[succ]
                    and (prev[succ] is None or nid < prev[succ])
                ):
                    dist[succ] = cand
                    prev[succ] = nid
        # fim do caminho: maior dist; desempate determinístico por id
        end = max(topo, key=lambda n: (dist[n], n))
        path: list[GraphNode] = []
        cur: str | None = end
        while cur is not None:
            path.append(self.graph.nodes[cur])
            cur = prev[cur]
        path.reverse()
        return path

    def _topological_order(self) -> list[str]:
        """Ordenação topológica (Kahn) do DAG, determinística por id.

        O(V+E) com fila min-heap por id (determinística, nunca O(V²)).
        Arestas para nós inexistentes são ignoradas (tolerância).
        """
        in_degree = {nid: 0 for nid in self.graph.nodes}
        adj: dict[str, list[str]] = {nid: [] for nid in self.graph.nodes}
        for edge in self.graph.edges:
            if edge.source in in_degree and edge.target in in_degree:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        # min-heap por id → ordem topológica determinística independente da
        # ordem de inserção do grafo (RF-G2B.3: puro e determinístico).
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        heapq.heapify(queue)
        order: list[str] = []
        while queue:
            nid = heapq.heappop(queue)
            order.append(nid)
            for succ in adj[nid]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    heapq.heappush(queue, succ)
        # Ciclo → todos os nós restantes têm in_degree > 0. Grafo é DAG por
        # construção (ADR-0004 §2.5); ciclo seria violação de invariante.
        if len(order) != len(self.graph.nodes):
            raise ValueError(
                "Grafo contém ciclo — invariante DAG violado (ADR-0004 §2.5)"
            )
        return order

    def _path_weight(self, node: GraphNode) -> float:
        """Peso do nó no caminho crítico (PRP-GRAPH-2B §3)."""
        if self.node_state(node.id) is NodeState.SKIPPED:
            return self._SKIPPED_WEIGHT
        if node.kind is NodeKind.GATE:
            return self._GATE_WEIGHT
        return self._STEP_WEIGHT

    def impact_of(self, node_id: str) -> set[str]:
        """Propagação descendente: todos os nós afetados por mudança em node_id.

        Base formal do Smart Skip e do Delta (Δ.0). Query pura (RF-G1B.5).
        Segue todas as arestas de saída (DEPENDS_ON/BLOCKS/REWORK/PRODUCES) —
        interpretação conservadora: na dúvida, marcar como afetado.
        """
        if self.graph.node(node_id) is None:
            raise KeyError(f"Nó não encontrado no grafo: {node_id}")
        affected: set[str] = set()
        stack = list(self.graph.successors(node_id))
        while stack:
            nid = stack.pop()
            if nid in affected:
                continue
            affected.add(nid)
            stack.extend(self.graph.successors(nid))
        return affected

    # ── Suporte interno ────────────────────────────────────────────────────
    def _has_edge_between(self, a: str, b: str) -> bool:
        """True se existe aresta entre a e b (qualquer kind, qualquer direção).

        Independência mútua (RF-G2A.2): dois nós com aresta entre si
        (DEPENDS_ON/PRODUCES/BLOCKS/REWORK) NUNCA podem estar juntos na
        frontier — rodar em paralelo violaria a ordem do DAG.
        """
        return any(
            (e.source == a and e.target == b) or (e.source == b and e.target == a)
            for e in self.graph.edges
        )

    def _deps_satisfied(self, node: GraphNode) -> bool:
        """Deps satisfeitas = toda dependência em DONE|SKIPPED (§2.12).

        A estrutura do DAG vive nas arestas (o builder não popula depends_on
        de steps/gates — só de retries): unimos node.depends_on (quando
        presente) com todos os sources de arestas de entrada, incluindo
        BLOCKS (§2.4: sucessor não READY enquanto o gate não aprovar).
        Dep órfã (nó inexistente) = bloqueada até resolvida — nunca READY.
        """
        deps = set(node.depends_on)
        for edge in self.graph.edges:
            if edge.target == node.id:
                deps.add(edge.source)
        return all(self._state_satisfied(dep) for dep in deps)

    def _state_satisfied(self, node_id: str) -> bool:
        """DONE|SKIPPED — satisfeito para fins de dependência (§2.12)."""
        if self.graph.node(node_id) is None:
            return False  # dependência órfã: bloqueada
        return self.node_state(node_id) in (NodeState.DONE, NodeState.SKIPPED)

    def _gate_decision(self, node: GraphNode) -> str | None:
        """Lê <gate_result> real (não-placeholder) da sessão do step gateado.

        Espelha o padrão de llc_wizard/data.py sem importá-lo (DIP): a decisão
        humana é gravada pelo harness/UserDecisionWriter no .md da sessão do
        step que o gate gateia. Comentários HTML (placeholders) são ignorados.
        """
        gated_step = self._gated_step(node)
        if gated_step is None:
            return None
        step_id = gated_step[len("step-"):] if gated_step.startswith("step-") \
            else gated_step
        latest = self._latest_session_for(step_id)
        if not latest:
            return None
        session_file = self._sessions_dir / f"{latest.get('session_id', '')}.md"
        if not session_file.exists():
            return None
        content = session_file.read_text(encoding="utf-8")
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        match = re.search(r'<gate_result[^>]*decision="(approved|rejected)"',
                          content)
        return match.group(1) if match else None

    def _gated_step(self, node: GraphNode) -> str | None:
        """Step gateado pelo gate: fonte da aresta DEPENDS_ON de entrada.

        O GraphBuilder cria nós de gate SEM depends_on (a estrutura do DAG
        vive nas arestas) — logo o step gateado é derivado das arestas,
        com fallback para depends_on (grafo construído à mão).
        """
        for edge in self.graph.edges:
            if edge.target == node.id and edge.kind == EdgeKind.DEPENDS_ON:
                return edge.source
        if node.depends_on:
            return node.depends_on[0]
        return None

    def _gate_for_step(self, step_id: str) -> GraphNode | None:
        """Nó GATE que gateia o step (inverso de `_gated_step`).

        Usado na paridade §7.6: o engine precisa saber se o step tem gate e
        qual a decisão real dele — sem duplicar a estrutura do DAG.
        """
        for node in self.graph.nodes.values():
            if node.kind == NodeKind.GATE and self._gated_step(node) == step_id:
                return node
        return None

    def step_gate_decision(self, step_id: str) -> str | None:
        """Decisão real do gate que gateia o step (paridade §7.6).

        O adapter GraphPipelineDataSource usa isto para mapear sessão
        in_progress + gate sem decisão → GATE_PENDING, espelhando o reader.
        """
        step_node = self.graph.node(f"step-{step_id}")
        if step_node is None:
            return None
        gate = self._gate_for_step(step_node.id)
        if gate is None:
            return None
        return self._gate_decision(gate)

    def _latest_session_for(self, step_id: str) -> dict | None:
        """Sessão mais recente do step (llc_step_id) no .ace/index.json."""
        index_path = self.root / ".ace" / "index.json"
        if not index_path.exists():
            return None
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        sessions = [
            s for s in data.get("sessions", [])
            if str(s.get("llc_step_id", "")) == step_id
        ]
        if not sessions:
            return None
        return max(sessions, key=lambda s: s.get("timestamp", ""))

    def session_timestamp(self, step_id: str) -> datetime:
        """Timestamp da última sessão ATIVA do step (RF-G1C.5 / SLA Kanban).

        Espelha PipelineDataReader.get_status_since (filtro por status ativos)
        para paridade de SLA no Kanban (RF-G1C.4). Epoch se não houver sessão
        ativa ou o timestamp for inválido.
        """
        index_path = self.root / ".ace" / "index.json"
        if not index_path.exists():
            return datetime.fromtimestamp(0)
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return datetime.fromtimestamp(0)
        sessions = [
            s for s in data.get("sessions", [])
            if str(s.get("llc_step_id", "")) == step_id
            and s.get("status") in ("in_progress", "completed", "failed")
        ]
        if not sessions:
            return datetime.fromtimestamp(0)
        latest = max(sessions, key=lambda s: s.get("timestamp", ""))
        ts = latest.get("timestamp", "")
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return datetime.fromtimestamp(0)
