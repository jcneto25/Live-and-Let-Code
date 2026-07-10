from .models import UnknownStepError, EPS, StepSpec
from .registry import REGISTRY, _ALIAS_MAP


def normalize_step(raw) -> "StepSpec":
    """Resolve qualquer forma de step no StepSpec canônico.

    Aceita: StepSpec (idempotente), int/float (casar por EPSILON, nunca ==),
    str (id canônico exato -> alias exato -> número-string via float()).
    Levanta UnknownStepError se não resolver.
    """
    if isinstance(raw, StepSpec):
        return raw
    # bool é subclasse de int — não é um step válido.
    if isinstance(raw, bool):
        raise UnknownStepError(f"Step inválido (booleano): {raw!r}")
    if isinstance(raw, (int, float)):
        value = float(raw)
        for spec in REGISTRY.values():
            if abs(value - spec.number) < EPS:
                return spec
        raise UnknownStepError(f"Nenhum step com número {value}")
    if isinstance(raw, str):
        s = raw.strip()
        if s in REGISTRY:
            return REGISTRY[s]
        if s in _ALIAS_MAP:
            return REGISTRY[_ALIAS_MAP[s]]
        try:
            return normalize_step(float(s))
        except ValueError:
            pass
        raise UnknownStepError(f"Step desconhecido: {raw!r}")
    raise UnknownStepError(f"Step desconhecido: {raw!r}")


def canonical_id(raw) -> str:
    """Id canônico (string numérica) de qualquer forma de step."""
    return normalize_step(raw).id


def pipeline_steps(from_id=None, to_id=None) -> list["StepSpec"]:
    """Steps in_pipeline ordenados por número, dentro do range [from_id, to_id].

    from_id/to_id aceitam qualquer forma resolúvel por normalize_step (ou None).
    """
    lo = normalize_step(from_id).number if from_id is not None else None
    hi = normalize_step(to_id).number if to_id is not None else None
    out: list["StepSpec"] = []
    for spec in sorted(REGISTRY.values(), key=lambda s: s.number):
        if not spec.in_pipeline:
            continue
        if lo is not None and spec.number < lo - EPS:
            continue
        if hi is not None and spec.number > hi + EPS:
            continue
        out.append(spec)
    return out
