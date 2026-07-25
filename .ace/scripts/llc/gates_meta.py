import click

# ── Mapeamento de aliases para IDs de gates ──
# Aliases reconhecidos pelo CLI `llc gate`. O gate de cobertura tem 3 nomes na
# base de conhecimento (guia "10-COVERAGE", config/id "10.8", CLI "test-coverage");
# todos resolvem para o mesmo id "10.8" para evitar confusão (E-11).
GATE_ALIASES = {
    "security": "11-SEC",
    "null-safety": "12-NULL",
    "owasp": "11-OWASP",
    "verify": "11.2",
    "test-coverage": "10.8",
    "10-coverage": "10.8",
    "secure-by-design": "5d",
    "tdd-discipline": "9a",
    "ux-heuristics": "7a",
    "devops-bootstrap": "10a",
}

# ── Tabela de gates e suas validações ──
GATE_CHECKLIST = {
    "11-SEC": {
        "name": "Security Audit (pre-code)",
        "checks": [
            "0 vulnerabilidades criticas (CVSS ≥ 9.0)",
            "Nenhum secret real exposto",
            "Vulnerabilidades altas revisadas e decisao registrada",
        ],
        "output_files": [
            ".ace/security/*.json",
            "docs/security/SECURITY_AUDIT_REPORT.md",
        ],
    },
    "12-NULL": {
        "name": "Null Safety (Data Contracts)",
        "checks": [
            "0 campos sem especificacao de nulabilidade",
            "0 endpoints sem schema de validacao",
            "Payload limits declarados nos PRPs",
        ],
        "output_files": ["docs/security/NULL_SAFETY_REPORT.md"],
    },
    "11-OWASP": {
        "name": "OWASP Hardening (post-code)",
        "checks": [
            "0 verificacoes OWASP 🔴 (criticas)",
            "Todas 🟡 (altas) com plano de correcao documentado",
        ],
        "output_files": ["docs/security/OWASP_HARDENING_REPORT.md"],
    },
    "11.2": {
        "name": "PRP Verify (aceite mecanico)",
        "checks": [
            "prp_verify --strict passou (0 CRITICAL)",
            "WARNs revisados",
            "Bypass LLC_PRP_NO_VERIFY nao ativo",
        ],
        "output_files": [],
    },
    "5d": {
        "name": "Secure-by-Design (design-time prevention)",
        "checks": [
            "As 10 hard gates fazem sentido para o dominio do projeto?",
            "Templates adaptados ao stack especifico?",
            "Fitness functions --check-security --strict passaram?",
            "ADR-018 criado e justificado?",
            "Excecoes documentadas?",
        ],
        "output_files": [
            "docs/architecture/adr/ADR-018-secure-by-design.md",
            ".ace/arch-config.yaml",
        ],
    },
    "10a": {
        "name": "DevOps Bootstrap (infrastructure generation)",
        "checks": [
            "CI pipeline esta funcional e passando (pelo menos lint + build + test)?",
            "Feature flags estao corretas para o dominio? Kill-switches criticos definidos?",
            "Observabilidade cobre os cenarios de falha relevantes (crash reporting + logging)?",
            "Dependabot configurado com frequencia adequada ao ciclo de sprint?",
            "SBOM gerado automaticamente no CI?",
            "DevOps checklist cobre todos os ambientes (dev, staging, prod)?",
            "Stack adaptation correta (Node/Python/Go — comandos batem com a realidade)?",
        ],
        "output_files": [
            ".github/workflows/ci.yml",
            "src/config/features.ts",
            "src/utils/observability.ts",
            ".github/dependabot.yml",
            "docs/DEVOPS_CHECKLIST.md",
        ],
    },
    "7a": {
        "name": "UX Heuristics & Personas (design-time UX enforcement)",
        "checks": [
            "As personas sao representativas do publico real do projeto?",
            "As 10 hard gates de UX fazem sentido para o tipo de aplicacao?",
            "Nielsen Checklist foi aplicado a pelo menos 1 tela como exercicio?",
            "Os 4 padroes de implementacao sao compativeis com o stack?",
            "Algum anti-padrao e particularmente relevante para este dominio?",
            "Excecoes documentadas?",
        ],
        "output_files": [
            "docs/skills/llc-step-7a-ux-heuristics.md",
            "docs/business/personas.md",
        ],
    },
    "9a": {
        "name": "TDD Discipline (test-first enforcement)",
        "checks": [
            "As 7 hard gates de TDD fazem sentido para o stack e dominio?",
            "Os padroes de mock (Test Data Builder, Constructor Injection) sao compativeis com a arquitetura?",
            "A equipe entende o ciclo RED → GREEN → REFACTOR com commits por fase?",
            "O campo tdd_phase esta configurado no context_seed das sessoes Step 11?",
            "O pre-commit hook pre-commit-tests.sh esta configurado e funcional?",
            "Excecoes documentadas?",
        ],
        "output_files": [
            "docs/skills/llc-step-9a-tdd-discipline.md",
        ],
    },
    "10.8": {
        "name": "Test Coverage Gate (pre-execution)",
        "checks": [
            "Cobertura global de statements ≥ 80%",
            "0 arquivos de implementação sem cobertura (CRITICAL)",
            "Cobertura de branches ≥ 70%, functions ≥ 80%, lines ≥ 80%",
            "Caminhos críticos (auth, payments, data mutations) ≥ 90%",
        ],
        "output_files": ["docs/testing/COVERAGE_REPORT.md"],
    },
}


def _get_gate_id(gate_name: str) -> str:
    """Converte nome/alias para ID do gate (lookup case-insensitive)."""
    return GATE_ALIASES.get(gate_name.lower(), gate_name)


def _show_gate_checklist(gate_id: str):
    """Exibe checklist do gate."""
    if gate_id not in GATE_CHECKLIST:
        click.echo(f"Gate {gate_id} não encontrado.")
        return

    gate = GATE_CHECKLIST[gate_id]
    click.echo(f"\n📋 Gate: {gate['name']} ({gate_id})")
    click.echo(f"{'=' * 50}")
    click.echo("\nChecklist de Validação:")
    for i, check in enumerate(gate["checks"], 1):
        click.echo(f"  {i}. {check}")

    if gate["output_files"]:
        click.echo("\nArquivos gerados:")
        for f in gate["output_files"]:
            click.echo(f"  • {f}")
