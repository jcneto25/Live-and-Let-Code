"""llc_graph.state — AceStateReader: estado derivado das sessões ACE.

ADR-0004 D1/P3: o estado do grafo NUNCA é fonte primária — é derivado das
sessões ACE (.ace/index.json). Se o cache de estado ficar inconsistente,
reconstrói-se a partir do ACE.
"""
from __future__ import annotations

import json
from pathlib import Path

from llc_graph.model import NodeState


class AceStateReader:
    """Deriva NodeState dos nós a partir de .ace/index.json (read-only)."""

    def __init__(self, project_root: Path | str | None = None,
                 index_path: Path | str | None = None):
        self.root = Path(project_root) if project_root else Path(".")
        self._index_path = (
            Path(index_path) if index_path else self.root / ".ace" / "index.json"
        )

    def _load_sessions(self) -> list[dict]:
        """Lê .ace/index.json; tolera ausência/corrupção (RF-G1A.6)."""
        if not self._index_path.exists():
            return []
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data.get("sessions", [])

    def node_state(self, node_id: str) -> NodeState:
        """Estado derivado do nó. Steps usam a sessão mais recente do step.

        RF-G1A.5: sessão completed → DONE.
        RF-G1A.6: index ausente → PENDING (sem exceção).
        """
        if not node_id.startswith("step-"):
            # gates/hitl/prp sem sessão direta permanecem PENDING nesta camada
            return NodeState.PENDING
        step_id = node_id[len("step-"):]
        sessions = self._load_sessions()
        step_sessions = [
            s for s in sessions if str(s.get("llc_step_id", "")) == step_id
        ]
        if not step_sessions:
            return NodeState.PENDING
        latest = max(step_sessions, key=lambda s: s.get("timestamp", ""))
        status = latest.get("status", "")
        if status in ("completed", "done"):
            return NodeState.DONE
        if status in ("failed", "rejected"):
            return NodeState.FAILED
        if status in ("in_progress", "running"):
            return NodeState.RUNNING
        return NodeState.PENDING
