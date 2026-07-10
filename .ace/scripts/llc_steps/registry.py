from .models import _spec

# Ordem das entradas == ordem do pipeline (apenas p/ legibilidade; a ordenação
# real usa `number`).
REGISTRY: dict[str, "StepSpec"] = {
    "0": _spec("0", "Ingestão", "llc-step-0-greenfield", None, False, False),
    "0.1": _spec("0.1", "Conversão (Docling)", "llc-step-0-1", None, False, False),
    "0.2": _spec(
        "0.2",
        "Delta Impact Analysis",
        "llc-step-delta-impact",
        "Δ.0",
        False,
        False,
        aliases=("delta-impact", "d-impact", "d-0"),
    ),
    "0.3": _spec(
        "0.3",
        "Delta Grill Me",
        "llc-step-delta-grill",
        "Δ.1",
        False,
        False,
        aliases=("delta-grill", "d-grill", "d-1"),
    ),
    "0.5": _spec("0.5", "Visão + Módulos", "llc-step-0-5", "1", True, False),
    "1": _spec("1", "7 Especificações", "llc-step-1", "2", True, False),
    "2": _spec("2", "PRDs", "llc-step-2", "3", True, False),
    "3": _spec("3", "PRPs", "llc-step-3", "4", True, False),
    "4": _spec("4", "Planejamento", "llc-step-4", "5", True, False),
    "5": _spec("5", "Arquitetura", "llc-step-5", "6", True, False),
    # Sub-steps de arquitetura (F-14: wirear sub-skills 5a/5b/5c):
    "5.1": _spec(
        "5.1",
        "Architecture Patterns",
        "llc-step-5a-architecture-patterns",
        "6a",
        True,
        False,
        aliases=("5a", "architecture-patterns", "arch-patterns"),
    ),
    "5.2": _spec(
        "5.2",
        "API Design Enforcement",
        "llc-step-5b-api-design",
        "6b",
        True,
        False,
        aliases=("5b", "api-design"),
    ),
    "5.3": _spec(
        "5.3",
        "Clean Code Enforcement",
        "llc-step-5c-clean-code",
        "8.5",
        True,
        False,
        aliases=("5c", "clean-code"),
    ),
    "6": _spec("6", "Tarefas", "llc-step-6", "7", True, False),
    "7": _spec("7", "Design System", "llc-step-7", "8", True, False),
    "8": _spec("8", "Setup + Mock Data", "llc-step-8", "9", True, False),
    # Sub-step de setup (F-14: wirear sub-skill 8b):
    "8.1": _spec(
        "8.1",
        "Repository Pattern Setup",
        "llc-step-8b-repository-pattern",
        "9b",
        True,
        False,
        aliases=("8b", "repository-pattern", "repo-pattern"),
    ),
    "9": _spec("9", "Documentação de Testes", "llc-step-9", "10", True, False),
    "10": _spec("10", "Documentos do Projeto", "llc-step-10", "11", True, False),
    "10.5": _spec("10.5", "User Guide", "llc-user-guide", "11.5", True, False),
    # Pós-docs / pré-execução (renumerados p/ preceder a execução por número):
    "10.6": _spec(
        "10.6",
        "Security Audit",
        "llc-step-11-security",
        "11-SEC",
        True,
        False,
        aliases=("11-security", "security", "11-sec"),
    ),
    "10.7": _spec(
        "10.7",
        "Null Safety",
        "llc-step-12-null-safety",
        "12-NULL",
        True,
        False,
        aliases=("12-null", "null-safety", "12-null-safety", "null"),
    ),
    "10.8": _spec(
        "10.8",
        "Test Coverage Gate",
        "llc-step-10-8-test-coverage",
        "10.8",
        True,
        False,
        aliases=("test-coverage", "test", "10-8-test-coverage", "10-coverage"),
    ),
    # Pré-execução: domain modeling per PRP (F-14: wirear sub-skill 11a):
    "10.9": _spec(
        "10.9",
        "Domain Modeling",
        "llc-step-11a-domain-modeling",
        "11-PRE",
        True,
        False,
        aliases=("11a", "domain-modeling", "domain-model"),
    ),
    # Execução (escreve código) — gate é o QA Checkpoint, sem checklist 👤 em gates.json:
    "11": _spec(
        "11", "Execução", "llc-step-11", None, True, True, aliases=("execution",)
    ),
    # Pós-execução (hardening de código):
    "11.1": _spec(
        "11.1",
        "OWASP Hardening",
        "llc-step-11-owasp-security",
        "11-OWASP",
        True,
        True,
        aliases=("11-owasp", "owasp", "11-owasp-security"),
    ),
    # Pós-execução / pré-merge (aceite mecânico de PRP — advisory skill, enforcement no session_end):
    "11.2": _spec(
        "11.2",
        "PRP Verify",
        "llc-step-11-2-prp-verify",
        "11-VERIFY",
        False,
        False,
        aliases=("prp-verify", "verify"),
    ),
    # Pós-execução / pré-merge (conformidade arquitetural — fitness functions):
    # F-14: skill atualizada para a versão detalhada (llc-step-11b-arch-fitness)
    "11.3": _spec(
        "11.3",
        "Architecture Fitness",
        "llc-step-11b-arch-fitness",
        "11-ARCH",
        False,
        False,
        aliases=("arch-fitness", "arch", "fitness", "11b"),
    ),
}

# Mapa reverso de aliases -> id canônico (construído uma vez na importação).
_ALIAS_MAP: dict[str, str] = {}
for _id, _spec_obj in REGISTRY.items():
    for _alias in _spec_obj.aliases:
        _ALIAS_MAP[_alias] = _id
del _id, _spec_obj, _alias


def all_choices() -> list[str]:
    """Ids + aliases ordenados — para mensagens de erro/ajuda da CLI."""
    choices = sorted(REGISTRY.keys())
    choices.extend(sorted(a for spec in REGISTRY.values() for a in spec.aliases))
    return choices
