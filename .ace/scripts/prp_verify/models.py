#!/usr/bin/env python3
"""Dataclasses de resultado do prp_verify."""

from dataclasses import asdict, dataclass, field

from .constants import CRITICAL, WARN


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    rf: str = ""  # RF-XXX.N quando aplicável
    file: str = ""


@dataclass
class VerifyResult:
    prp: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def critical(self) -> int:
        return sum(1 for f in self.findings if f.severity == CRITICAL)

    @property
    def warns(self) -> int:
        return sum(1 for f in self.findings if f.severity == WARN)

    def to_dict(self) -> dict:
        return {
            "prp": self.prp,
            "critical": self.critical,
            "warn": self.warns,
            "findings": [asdict(f) for f in self.findings],
        }
