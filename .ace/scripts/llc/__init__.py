from .cli import cli


def main():
    """Ponto de entrada do CLI `llc` (equivalente a `cli()`)."""
    return cli()


__all__ = ["cli", "main"]
