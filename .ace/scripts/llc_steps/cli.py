# Click ParamType — definido só se click estiver disponível (scripts argparse
# não dependem de click).
StepParamType = None

try:
    import click
except ImportError:  # pragma: no cover
    click = None

if click is not None:
    from .models import UnknownStepError
    from .normalize import canonical_id

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

    from .registry import REGISTRY
