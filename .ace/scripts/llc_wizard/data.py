"""llc_wizard.data — camada de acesso read-only ao estado do pipeline.

RF-W1A.1–RF-W1A.5 — StepStatus, StepInfo, GateItem, GateInfo, PipelineStatus,
PipelineDataReader (+ Protocol PipelineDataSource para compatibilidade futura
com GraphEngine, RNF-W1A.8 / ADR-0004 §2.3).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol, Optional

from llc_steps.registry import REGISTRY


class StepStatus(str, Enum):
    """Os 7 estados possíveis de um step do pipeline (RF-W1A.1)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GATE_PENDING = "gate_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class StepInfo:
    """Informação imutável de um step do pipeline (RF-W1A.2)."""

    id: str
    name: str
    status: StepStatus
    in_pipeline: bool
    depends_on: list[str] = field(default_factory=list)
    current_session_id: str | None = None
    artifacts_output: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GateItem:
    """Item de checklist de um gate (RF-W1A.5 / GOV-003/R4).

    gates.json armazena checklists como listas de strings; todo item é
    required=true por default (§7.2). checked parte como False.
    """

    id: str
    description: str
    required: bool = True
    checked: bool = False


@dataclass(frozen=True)
class GateInfo:
    """Gate com seus itens de checklist e avaliação agregada (RF-W1A.5)."""

    id: str
    items: list[GateItem]

    @property
    def all_required_met(self) -> bool:
        """True se todos os itens required estão checked."""
        required_items = [i for i in self.items if i.required]
        if not required_items:
            return True
        return all(i.checked for i in required_items)


@dataclass(frozen=True)
class PipelineStatus:
    """Visão agregada do pipeline — progresso derivado dos steps (RF-W1A.3)."""

    steps: list[StepInfo]

    @property
    def progress_percent(self) -> float:
        """Percentual de steps completed sobre o total in_pipeline.

        Steps com in_pipeline=False (excluídos) não contam no denominador.
        """
        pipeline = [s for s in self.steps if s.in_pipeline]
        if not pipeline:
            return 0.0
        done = sum(1 for s in pipeline if s.status == StepStatus.COMPLETED)
        return round(done / len(pipeline) * 100, 1)


@dataclass(frozen=True)
class PendingHITL:
    """Decisão humana pendente (gate/question/artifact_review) — §7.4."""

    id: str
    step_id: str
    session_id: str
    kind: str
    summary: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


class PipelineDataSource(Protocol):
    """Contrato que PipelineDataReader implementa hoje e GraphEngine-backed
    reader implementará na Fase 3 (ADR-0004). Manter este Protocol estável
    evita retrabalho na refatoração do KanbanBoardBuilder (RNF-W1A.8)."""

    def get_status(self) -> "PipelineStatus": ...

    def get_gate_for_step(self, step_id: str) -> Optional["GateInfo"]: ...

    def get_status_since(self, step_id: str) -> datetime: ...

    def get_pending_hitl(self) -> list["PendingHITL"]: ...


class PipelineDataReader:
    """Reader read-only do estado do pipeline.

    Lê o REGISTRY (llc_steps), `.ace/index.json` (sessões) e
    `.ace/config/gates.json`. Deriva StepStatus pela tabela §7.6 (GOV-003/R4).
    Nunca escreve no disco (P1).
    """

    def __init__(self, project_root: Path):
        self.root = Path(project_root)
        self._index_path = self.root / ".ace" / "index.json"
        self._gates_path = self.root / ".ace" / "config" / "gates.json"

    def _load_index(self) -> list[dict]:
        if not self._index_path.exists():
            return []
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            return data.get("sessions", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _load_gates(self) -> dict:
        if not self._gates_path.exists():
            return {}
        try:
            data = json.loads(self._gates_path.read_text(encoding="utf-8"))
            return data.get("gates", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _gate_decision_from_session(self, session: dict) -> str | None:
        """Lê o <gate_result> real (não-placeholder) do arquivo .md da sessão.

        O <gate_result> é gravado pelo harness (_record_gate_result) na seção
        ## Gates do arquivo da sessão. Retorna a decision (approved/rejected)
        ou None se a sessão não tiver arquivo/resultado real (ex.: fluxo CLI
        puro, onde o gate roda síncrono no mesmo processo).
        """
        import re

        session_id = session.get("session_id")
        if not session_id:
            return None
        session_file = self.root / ".ace" / "sessions" / f"{session_id}.md"
        if not session_file.exists():
            return None
        content = session_file.read_text(encoding="utf-8")
        # remove comentários HTML (<!-- ... -->) para ignorar placeholders
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        m = re.search(r'<gate_result[^>]*decision="(approved|rejected)"', content)
        if not m:
            return None
        return m.group(1)

    def get_steps(self) -> list[StepInfo]:
        sessions = self._load_index()
        gates = self._load_gates()
        steps: list[StepInfo] = []
        for spec in REGISTRY.values():
            status = self._derive_status(spec, sessions, gates)
            info = StepInfo(
                id=spec.id,
                name=spec.name,
                status=status,
                in_pipeline=spec.in_pipeline,
            )
            steps.append(info)
        return steps

    def get_status(self) -> "PipelineStatus":
        return PipelineStatus(steps=self.get_steps())

    def _derive_status(self, spec, sessions, gates) -> StepStatus:
        """Deriva StepStatus pela tabela §7.6 (ordem de precedência)."""
        # 6. excluded (absoluto — fora do pipeline)
        if not spec.in_pipeline:
            return StepStatus.EXCLUDED
        # 5. skipped — skip note presente (Smart Skip)
        skip_note = self.root / "docs" / "delta" / "skip-notes" / f"step-{spec.id}.md"
        if skip_note.exists():
            return StepStatus.SKIPPED
        # 1-4. sessão mais recente do step
        step_sessions = [s for s in sessions if str(s.get("llc_step_id", "")) == spec.id]
        if not step_sessions:
            return StepStatus.PENDING  # 7. pending
        last = max(step_sessions, key=lambda s: s.get("timestamp", ""))
        last_status = last.get("status")
        decision = self._gate_decision_from_session(last)
        if last_status in ("completed", "done"):
            # 1. failed se gate foi rejeitado; 2. completed caso contrário
            if decision == "rejected":
                return StepStatus.FAILED
            return StepStatus.COMPLETED
        if last_status in ("failed", "rejected"):
            return StepStatus.FAILED  # 1. failed
        if last_status == "in_progress":
            # 3. gate_pending se o step tem gate e não há <gate_result> na sessão
            if spec.gate and spec.gate in gates and decision is None:
                return StepStatus.GATE_PENDING
            return StepStatus.IN_PROGRESS  # 4. in_progress
        return StepStatus.PENDING

    def get_gate_for_step(self, step_id: str) -> Optional["GateInfo"]:
        gates = self._load_gates()
        gate_def = gates.get(step_id)
        if not gate_def:
            return None
        items: list[GateItem] = []
        checklist = gate_def.get("checklist", []) if isinstance(gate_def, dict) else gate_def
        for idx, text in enumerate(checklist, start=1):
            items.append(GateItem(id=str(idx), description=str(text)))
        return GateInfo(id=step_id, items=items)

    def get_status_since(self, step_id: str) -> datetime:
        sessions = self._load_index()
        step_sessions = [s for s in sessions if s.get("llc_step_id") == step_id and s.get("status") in ("in_progress", "completed", "failed")]
        if not step_sessions:
            return datetime.fromtimestamp(0)
        last = max(step_sessions, key=lambda s: s.get("timestamp", ""))
        ts = last.get("timestamp", "")
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return datetime.fromtimestamp(0)

    def get_pending_hitl(self) -> list["PendingHITL"]:
        return []