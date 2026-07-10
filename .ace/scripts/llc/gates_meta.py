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
