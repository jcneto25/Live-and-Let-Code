#!/usr/bin/env python3
"""Pre/post-wave validation: baseline build, backend contracts, PRP acceptance."""

import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .models import PrpInfo

logger = logging.getLogger(__name__)

PRE_WAVE_CHECK_SCRIPT = Path(".ace") / "scripts" / "pre-wave-check.sh"

# UI-related keywords to detect Trilha B PRPs
UI_KEYWORDS = [
    "tela",
    "componente",
    "frontend",
    "ui",
    "dashboard",
    "página",
    "page",
    "view",
    "formulário",
    "form",
    "protótipo",
    "prototype",
    "wireframe",
    "design system",
    "design-system",
    "component",
    "screen",
]


def _is_ui_prp(prp_id: str, prp_info: PrpInfo) -> bool:
    """Verifica se um PRP envolve UI (Trilha B).

    Checa o nome do PRP e suas tasks por palavras-chave de UI.
    """
    # Check PRP name
    name_lower = (prp_info.name or "").lower()
    for kw in UI_KEYWORDS:
        if kw.lower() in name_lower:
            return True

    # Check tasks
    for task in prp_info.tasks:
        task_lower = task.lower()
        for kw in UI_KEYWORDS:
            if kw.lower() in task_lower:
                return True

    return False


def _load_stub_detector():
    """Carrega is_stub_service de consistency-check.py (sem import rígido)."""
    try:
        spec = importlib.util.spec_from_file_location(
            "consistency_check",
            Path.cwd() / ".ace" / "scripts" / "consistency-check.py",
        )
        if spec and spec.loader:
            cc = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cc)
            return cc.is_stub_service
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"   ⚠️  Não foi possível carregar consistency-check: {e}")
    return None


def _verify_backend_contracts(
    prp_id: str, prp_info: PrpInfo, dry_run: bool = False
) -> bool:
    """Verifica se os contratos de backend/API existem para um PRP com UI.

    Para Trilha B (UI), o backend deve ter:
    - Services implementados (não stubs)
    - Endpoints de API definidos
    - Schemas de validação

    Retorna True se contratos existem ou em dry-run.
    """
    if dry_run:
        logger.info(f"   [dry-run] Verificaria contratos de backend para {prp_id}")
        return True

    logger.info(f"🔍 Verificando contratos de backend para {prp_id} (API-first)...")

    is_stub_service = _load_stub_detector()

    api_dir = Path.cwd() / "api"
    contracts_found = False
    stubs_found = []

    # Try to find backend services for this PRP
    # Pattern 1: Check for service files in api/ that match PRP pattern
    if api_dir.exists():
        for ext in ["*.ts", "*.py", "*.go", "*.rs"]:
            for service_file in api_dir.rglob(ext):
                rel_path = service_file.relative_to(api_dir)
                rel_str = str(rel_path)

                # Check if this service relates to the PRP
                prp_keywords = _prp_to_keywords(prp_id)
                for kw in prp_keywords:
                    if kw.lower() in rel_str.lower():
                        contracts_found = True
                        if is_stub_service and is_stub_service(rel_path, api_dir):
                            stubs_found.append(rel_str)
                        else:
                            logger.info(f"   ✅ Contrato encontrado: {rel_str}")

    # Also check for OpenAPI/Swagger specs
    openapi_files = (
        list(Path.cwd().rglob("openapi*.yaml"))
        + list(Path.cwd().rglob("openapi*.yml"))
        + list(Path.cwd().rglob("swagger*.yaml"))
        + list(Path.cwd().rglob("swagger*.yml"))
    )
    for spec_file in openapi_files:
        contracts_found = True
        logger.info(
            f"   ✅ Spec OpenAPI encontrada: {spec_file.relative_to(Path.cwd())}"
        )

    if not contracts_found:
        logger.warning(f"   ⚠️  Nenhum contrato de backend/API detectado para {prp_id}.")
        logger.warning(
            "   Para Trilha B (UI), recomenda-se ter os contratos de API definidos "
            "antes de iniciar o frontend."
        )
        # Don't block, just warn - could be a new project
        return True

    if stubs_found:
        logger.error(f"   ❌ Contratos de backend são STUBS para {prp_id}:")
        for stub in stubs_found:
            logger.error(f"      - {stub}")
        logger.error(
            "   API-first: Implemente os services de backend antes de iniciar a UI."
        )
        return False

    logger.info(f"✅ Contratos de backend verificados para {prp_id}")
    return True


def _prp_to_keywords(prp_id: str) -> list[str]:
    """Mapeia PRP para palavras-chave de serviço/backend.

    Baseado no PRP_SERVICE_MAP do consistency-check.py.
    """
    mapping = {
        "PRP-001": ["auth", "usuarios", "users"],
        "PRP-002": ["perfis", "profiles"],
        "PRP-003": ["universo", "universe"],
        "PRP-004": ["planos", "plans"],
        "PRP-005": ["auditorias", "audits"],
        "PRP-006": ["achados", "findings"],
        "PRP-007": ["relatorios", "reports"],
        "PRP-008": ["recomendacoes", "recommendations"],
        "PRP-009": ["etica", "ethics"],
        "PRP-010": ["consultorias", "consulting"],
        "PRP-011": ["qualidade", "quality"],
        "PRP-012": ["riscos", "risks"],
        "PRP-013": ["governanca", "governance"],
        "PRP-014": ["dashboards", "dashboard"],
    }
    return mapping.get(prp_id, [])


def _run_bash_script(script: Path, *args: str) -> subprocess.CompletedProcess:
    """Executa um script bash do pipeline capturando stdout/stderr."""
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )


def _pre_wave_check(dry_run: bool = False, wave_num: int = 0) -> bool:
    """Executa validacao de prontidao antes de iniciar a onda (build + bootstrap + health).

    Retorna True se passou ou se o script nao existe (projeto sem stack executavel).
    """
    if not PRE_WAVE_CHECK_SCRIPT.exists():
        logger.info("ℹ️  pre-wave-check.sh nao encontrado — pulando validacao pre-onda.")
        return True

    if dry_run:
        logger.info("   [dry-run] pre-wave-check seria executado")
        return True

    logger.info(f"\n{'─' * 50}")
    logger.info("🔍 Pre-Wave Check — validando baseline antes da onda")

    result = _run_bash_script(PRE_WAVE_CHECK_SCRIPT, "--build-only", "--timeout", "30")
    for line in result.stdout.split("\n"):
        if line.strip():
            logger.info(f"   {line.strip()}")

    if result.returncode == 0:
        logger.info("✅ Pre-Wave Check: baseline OK")
        return True
    logger.error(f"❌ Pre-Wave Check FALHOU (exit: {result.returncode})")
    logger.error(f"   Corrija os erros de compilacao antes de iniciar a onda.")
    return False


def _post_wave_check(
    dry_run: bool = False, wave_num: int = 0, prp_ids: Optional[list[str]] = None
) -> bool:
    """Executa validacao pos-onda: build + bootstrap + health + consistency + aceite de PRP.

    Retorna True se passou; retorna False se prp_verify encontrar CRITICAL
    (bloqueia a onda). build/bootstrap/health e consistency-check permanecem
    advisory (warnings).

    O bloco de aceite de PRP (prp_verify CRITICAL) é INDEPENDENTE da existência
    de pre-wave-check.sh (M-02): um projeto sem stack executável ainda assim
    tem sua aceitação mecânica de PRP verificada.
    """
    if dry_run:
        logger.info("   [dry-run] post-wave-check seria executado")
        return True

    _post_wave_build_health()
    _post_wave_consistency()
    return _post_wave_prp_acceptance(prp_ids)


def _post_wave_build_health() -> None:
    """Build/bootstrap/health pós-onda (advisory). Não bloqueia a onda."""
    if not PRE_WAVE_CHECK_SCRIPT.exists():
        logger.info(
            "ℹ️  pre-wave-check.sh nao encontrado — pulando validacao de build pos-onda."
        )
        return

    logger.info(f"\n{'─' * 50}")
    logger.info("🔍 Post-Wave Check — validando integridade apos a onda")

    result = _run_bash_script(PRE_WAVE_CHECK_SCRIPT, "--timeout", "30")
    for line in result.stdout.split("\n"):
        if line.strip():
            logger.info(f"   {line.strip()}")

    if result.returncode == 0:
        logger.info("✅ Post-Wave Check: todos os checks OK")
    else:
        logger.warning(f"⚠️  Post-Wave Check: {result.returncode} check(s) falharam")
        logger.warning(
            "   A onda foi concluida, mas ha problemas de build/bootstrap/health."
        )
        logger.warning(
            "   Registre como blocker e corrija antes de iniciar a proxima onda."
        )


def _post_wave_consistency() -> None:
    """Verificação de consistência TASKS.md × código (advisory)."""
    consistency_script = Path(".ace") / "scripts" / "consistency-check.py"
    if not consistency_script.exists():
        logger.info(
            "ℹ️  consistency-check.py nao encontrado — pulando verificacao de consistencia."
        )
        return

    logger.info(f"\n{'─' * 50}")
    logger.info("📋 Verificando consistencia TASKS.md × codigo...")
    result_cc = subprocess.run(
        ["python3", str(consistency_script)],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    for line in result_cc.stdout.split("\n"):
        if line.strip() and not line.startswith("="):
            logger.info(f"   {line.strip()}")
    if result_cc.returncode != 0 and result_cc.stderr:
        for line in result_cc.stderr.strip().split("\n"):
            logger.warning(f"   {line.strip()}")
    else:
        logger.info("✅ Consistencia OK — documentacao reflete o codigo.")


def _post_wave_prp_acceptance(prp_ids: Optional[list[str]]) -> bool:
    """Aceite mecânico de PRP (Step 11.2) — BLOQUEANTE em CRITICAL.

    Independente de pre-wave-check.sh (M-02). Retorna False se algum PRP
    tiver pendências CRITICAL.
    """
    if os.environ.get("LLC_PRP_NO_VERIFY") == "1":
        logger.info("ℹ️  prp_verify bypassado via LLC_PRP_NO_VERIFY=1.")
        return True

    verify_script = Path(".ace") / "scripts" / "prp_verify.py"
    if not prp_ids or not verify_script.exists():
        return True

    logger.info(f"\n{'─' * 50}")
    logger.info("📋 Verificando aceite mecânico dos PRPs (prp_verify)...")
    critical_found = False
    for prp_id in prp_ids:
        rv = subprocess.run(
            [
                "python3",
                str(verify_script),
                "--prp",
                prp_id,
                "--strict",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        if rv.returncode == 2:
            critical_found = True
            try:
                n = json.loads(rv.stdout).get("critical", "?")
            except (json.JSONDecodeError, TypeError):
                n = "?"
            logger.error(
                f"⛔ {prp_id}: prp_verify CRITICAL ({n} pendência(s) bloqueante(s))"
            )
    if critical_found:
        logger.error("⛔ Onda BLOQUEADA — prp_verify encontrou CRITICAL.")
        logger.error(
            "   Corrija as pendências ou use bypass explícito: LLC_PRP_NO_VERIFY=1."
        )
        return False
    logger.info("✅ prp_verify limpo para todos os PRPs da onda.")
    return True
