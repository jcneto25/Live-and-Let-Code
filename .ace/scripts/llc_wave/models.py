#!/usr/bin/env python3
"""Data structures for the LLC wave executor."""

from typing import Optional


class WaveInfo:
    """Informacao de uma onda de execucao."""

    def __init__(self, number: int, name: str, prps: list[str]):
        self.number: int = number
        self.name: str = name
        self.prps: list[str] = list(prps)

    def __repr__(self):
        return f"Wave {self.number}: {self.name} ({len(self.prps)} PRPs)"


class PrpInfo:
    """Informacao de um PRP."""

    def __init__(self, prp_id: str, name: str = "", tasks: Optional[list[str]] = None):
        self.prp_id: str = prp_id
        self.name: str = name
        # Cópia defensiva: o chamador pode continuar mutando sua lista.
        self.tasks: list[str] = list(tasks) if tasks is not None else []

    def __repr__(self):
        return f"{self.prp_id}: {self.name} ({len(self.tasks)} tasks)"
