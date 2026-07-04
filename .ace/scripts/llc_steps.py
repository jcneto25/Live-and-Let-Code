#!/usr/bin/env python3
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

O id canônico é a STRING numérica de sequência ("10.6"), armazenada em
`llc_step_id`. `llc_step` (float) é a projeção numérica p/ leitores legados que
fazem float(). Slugs semânticos ("security", "11-security") e nomes de skill
permanecem como ALIASES e como `skill_file` — não são renumerados.
"""

from dataclasses import dataclass, field

# Tolerância para igualdade de floats (10.6, 10.7, 11.1 não são exatos).
EPS = 1e-9


class UnknownStepError(ValueError):
    """Levantado quando um valor não resolve para nenhum step conhecido."""


@dataclass(frozen=True)
class StepSpec:
    id: str                 # id canônico = string numérica de sequência, ex. "10.6"
    number: float           # projeção numérica (== float do id)
    name: str               # nome humano (mantém convenção PT do LLC_STEPS antigo)
    skill_file: str | None  # stem do arquivo de skill (sem .md), ex. "llc-step-11-security"
    gate: str | None        # chave em gates.json `gates`, ex. "11-SEC" (ou None)
    in_pipeline: bool       # entra na sequência automática do pipeline_run
    auto_worktree: bool     # cria git worktree isolado por padrão
    aliases: tuple[str, ...] = field(default_factory=tuple)


def _spec(id_: str, name: str, skill_file: str | None, gate: str | None,
          in_pipeline: bool, auto_worktree: bool, aliases=()) -> StepSpec:
    return StepSpec(id=id_, number=float(id_), name=name, skill_file=skill_file,
                    gate=gate, in_pipeline=in_pipeline, auto_worktree=auto_worktree,
                    aliases=tuple(aliases))


# Ordem das entradas == ordem do pipeline (apenas p/ legibilidade; a ordenação
# real usa `number`).
REGISTRY: dict[str, StepSpec] = {
    "0":    _spec("0",    "Ingestão",                None,                     None,      False, False),
    "0.1":  _spec("0.1",  "Conversão (Docling)",     "llc-step-0-1",           None,      False, False),
    "0.5":  _spec("0.5",  "Visão + Módulos",         "llc-step-0-5",           "1",       True,  False),
    "1":    _spec("1",    "7 Especificações",        "llc-step-1",             "2",       True,  False),
    "2":    _spec("2",    "PRDs",                    "llc-step-2",             "3",       True,  False),
    "3":    _spec("3",    "PRPs",                    "llc-step-3",             "4",       True,  False),
    "4":    _spec("4",    "Planejamento",            "llc-step-4",             "5",       True,  False),
    "5":    _spec("5",    "Arquitetura",             "llc-step-5",             "6",       True,  False),
    "6":    _spec("6",    "Tarefas",                 "llc-step-6",             "7",       True,  False),
    "7":    _spec("7",    "Design System",           "llc-step-7",             "8",       True,  False),
    "8":    _spec("8",    "Setup + Mock Data",       "llc-step-8",             "9",       True,  False),
    "9":    _spec("9",    "Documentação de Testes",  "llc-step-9",             "10",      True,  False),
    "10":   _spec("10",   "Documentos do Projeto",   "llc-step-10",            "11",      True,  False),
    "10.5": _spec("10.5", "User Guide",              "llc-user-guide",         "11.5",    True,  False),
    # Pós-docs / pré-execução (renumerados p/ preceder a execução por número):
    "10.6": _spec("10.6", "Security Audit",          "llc-step-11-security",   "11-SEC",  True,  False,
                  aliases=("11-security", "security", "11-sec")),
    "10.7": _spec("10.7", "Null Safety",             "llc-step-12-null-safety","12-NULL", True,  False,
                  aliases=("12-null", "null-safety", "12-null-safety", "null")),
    # Execução (escreve código) — gate é o QA Checkpoint, sem checklist 👤 em gates.json:
    "11":   _spec("11",   "Execução",                "llc-step-11",            None,      True,  True,
                  aliases=("execution",)),
    # Pós-execução (hardening de código):
    "11.1": _spec("11.1", "OWASP Hardening",         "llc-step-11-owasp-security", "11-OWASP", True, True,
                  aliases=("11-owasp", "owasp", "11-owasp-security")),
    # Pós-execução / pré-merge (aceite mecânico de PRP — advisory skill, enforcement no session_end):
    "11.2": _spec("11.2", "PRP Verify",              "llc-step-11-2-prp-verify",  "11-VERIFY", False, False,
                  aliases=("prp-verify", "verify")),
}

# Mapa reverso de aliases -> id canônico (construído uma vez na importação).
_ALIAS_MAP: dict[str, str] = {}
for _id, _spec_obj in REGISTRY.items():
    for _alias in _spec_obj.aliases:
        _ALIAS_MAP[_alias] = _id
del _id, _spec_obj, _alias


def normalize_step(raw) -> StepSpec:
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


def pipeline_steps(from_id=None, to_id=None) -> list[StepSpec]:
    """Steps in_pipeline ordenados por número, dentro do range [from_id, to_id].

    from_id/to_id aceitam qualquer forma resolúvel por normalize_step (ou None).
    """
    lo = normalize_step(from_id).number if from_id is not None else None
    hi = normalize_step(to_id).number if to_id is not None else None
    out: list[StepSpec] = []
    for spec in sorted(REGISTRY.values(), key=lambda s: s.number):
        if not spec.in_pipeline:
            continue
        if lo is not None and spec.number < lo - EPS:
            continue
        if hi is not None and spec.number > hi + EPS:
            continue
        out.append(spec)
    return out


def all_choices() -> list[str]:
    """Ids + aliases ordenados — para mensagens de erro/ajuda da CLI."""
    choices = sorted(REGISTRY.keys())
    choices.extend(sorted(a for spec in REGISTRY.values() for a in spec.aliases))
    return choices


# Click ParamType — definido só se click estiver disponível (scripts argparse
# não dependem de click).
try:
    import click
except ImportError:  # pragma: no cover
    click = None

if click is not None:
    class StepParamType(click.ParamType):
        name = "step"

        def convert(self, value, param, ctx):
            try:
                return canonical_id(value)
            except UnknownStepError:
                self.fail(
                    f"{value!r} não é um step LLC válido. "
                    f"Válidos: {', '.join(sorted(REGISTRY))} "
                    f"(aliases: security, owasp, null-safety).",
                    param,
                    ctx,
                )


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            try:
                s = normalize_step(arg)
                print(f"{arg!r:>22} -> id={s.id:<5} num={s.number:<5} "
                      f"skill={s.skill_file} gate={s.gate}")
            except UnknownStepError as e:
                print(f"{arg!r:>22} -> ERRO: {e}")
    else:
        print(json.dumps(
            {s.id: {"number": s.number, "name": s.name, "skill_file": s.skill_file,
                    "gate": s.gate, "in_pipeline": s.in_pipeline,
                    "auto_worktree": s.auto_worktree, "aliases": list(s.aliases)}
             for s in sorted(REGISTRY.values(), key=lambda x: x.number)},
            indent=2, ensure_ascii=False))
