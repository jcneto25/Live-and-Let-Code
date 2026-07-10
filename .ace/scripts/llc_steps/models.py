from dataclasses import dataclass, field

# Tolerância para igualdade de floats (10.6, 10.7, 11.1 não são exatos).
EPS = 1e-9


class UnknownStepError(ValueError):
    """Levantado quando um valor não resolve para nenhum step conhecido."""


@dataclass(frozen=True)
class StepSpec:
    id: str  # id canônico = string numérica de sequência, ex. "10.6"
    number: float  # projeção numérica (== float do id)
    name: str  # nome humano (mantém convenção PT do LLC_STEPS antigo)
    skill_file: (
        str | None
    )  # stem do arquivo de skill (sem .md), ex. "llc-step-11-security"
    gate: str | None  # chave em gates.json `gates`, ex. "11-SEC" (ou None)
    in_pipeline: bool  # entra na sequência automática do pipeline_run
    auto_worktree: bool  # cria git worktree isolado por padrão
    aliases: tuple[str, ...] = field(default_factory=tuple)


def _spec(
    id_: str,
    name: str,
    skill_file: str | None,
    gate: str | None,
    in_pipeline: bool,
    auto_worktree: bool,
    aliases=(),
) -> StepSpec:
    return StepSpec(
        id=id_,
        number=float(id_),
        name=name,
        skill_file=skill_file,
        gate=gate,
        in_pipeline=in_pipeline,
        auto_worktree=auto_worktree,
        aliases=tuple(aliases),
    )
