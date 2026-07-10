"""
llc_steps — fonte única de verdade para a identidade de steps do pipeline LLC.

Resolve o descompasso entre steps NUMÉRICOS (floats no código: --step,
LLC_STEPS, pipeline_run, index.json `llc_step`) e steps TEXTUAIS (labels em
gates.json `step_to_gate` e nomes de skill). Após o renumero, o NÚMERO do step
== sua posição na sequência do pipeline, então todo step tem um float canônico:

    11-security -> 10.6   12-null -> 10.7   11 (execução) -> 11   11-owasp -> 11.1

API pública:
    StepSpec                  — registro imutável de um step
    REGISTRY                  — {id_canônico(str): StepSpec}
    normalize_step(raw)       — aceita StepSpec|float|int|str (id/alias/número)
                                e devolve o StepSpec; levanta UnknownStepError
    canonical_id(raw)         — normalize_step(raw).id
    pipeline_steps(from, to)  — steps in_pipeline ordenados por número, no range

Regra DURA: nunca comparar `llc_step` por igualdade (10.6/10.7/11.1 não são
exatos em IEEE-754). Floats casam por EPSILON; ordenação só via </>.
"""

from .models import EPS, StepSpec, UnknownStepError, _spec
from .registry import REGISTRY, _ALIAS_MAP, all_choices
from .normalize import normalize_step, canonical_id, pipeline_steps
from .cli import StepParamType

__all__ = [
    "EPS",
    "StepSpec",
    "UnknownStepError",
    "_spec",
    "REGISTRY",
    "_ALIAS_MAP",
    "all_choices",
    "normalize_step",
    "canonical_id",
    "pipeline_steps",
    "StepParamType",
]
