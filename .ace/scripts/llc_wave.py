#!/usr/bin/env python3
"""
llc_wave — Wave execution orchestrator for the Live and Let Code pipeline.

Parses EXECUTION_WAVES.md to discover wave → PRP mappings, then iterates
PRPs/tasks of a wave, opening individual ACE sessions per PRP or one
aggregated session.

Commands:
  wave list                    List all waves and their PRPs
  wave run --wave N            Execute wave N (one session per PRP)
  wave run --wave N --aggregate  Single aggregated session for wave N

Uso:
  llc wave list
  llc wave run --wave 1
  llc wave run --wave 1 --aggregate --dry-run
"""

import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ──

EXECUTION_WAVES_FILE = Path("docs/planning/EXECUTION_WAVES.md")
TASKS_FILE = Path("docs/planning/TASKS.md")


# ── Data structures ──


class WaveInfo:
    """Informacao de uma onda de execucao."""

    def __init__(self, number: int, name: str, prps: list[str]):
        self.number: int = number
        self.name: str = name
        self.prps: list[str] = prps

    def __repr__(self):
        return f"Wave {self.number}: {self.name} ({len(self.prps)} PRPs)"


class PrpInfo:
    """Informacao de um PRP."""

    def __init__(self, prp_id: str, name: str = "", tasks: Optional[list[str]] = None):
        self.prp_id: str = prp_id
        self.name: str = name
        self.tasks: list[str] = tasks if tasks is not None else []

    def __repr__(self):
        return f"{self.prp_id}: {self.name} ({len(self.tasks)} tasks)"


# ── Parsers ──


def _strip_placeholders(text: str) -> str:
    """Remove placeholders do template (ex: {N}, {Nome}, {Foundation})."""
    return re.sub(r"\{[^}]+\}", "", text)


def _find_wave_headings(content: str) -> list[tuple[int, int, str, int]]:
    """Encontra headings `### Onda N: Nome` e retorna lista de
    (start_line, heading_line, name, wave_number)."""
    results: list[tuple[int, int, str, int]] = []
    lines: list[str] = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"###\s+Onda\s+(\d+)\s*:\s*(.+)", line.strip())
        if m:
            num = int(m.group(1))
            name = m.group(2).strip().rstrip()
            # Pula se for placeholder (ex: "{Nome da Onda}")
            if re.fullmatch(r"\{[^}]+\}", name):
                name = ""
            results.append((i, i, name, num))
    return results


def parse_execution_waves(filepath: Path = EXECUTION_WAVES_FILE) -> list[WaveInfo]:
    """Parse EXECUTION_WAVES.md e retorna lista de WaveInfo.

    Busca headings `### Onda N: Nome` e extrai PRPs da primeira coluna
    de tabelas markdown encontradas no corpo da seção.

    NOTA: Requer um arquivo REAL gerado pelo Step 4 (llc-step-4).
    O template (EXECUTION_WAVES_TEMPLATE.md) tem placeholders `{N}` que
    não podem ser parseados — a feature só funciona após o planejamento.
    """
    if not filepath.exists():
        logger.error(
            f"Arquivo nao encontrado: {filepath}\n\n"
            "O comando `wave` requer um arquivo EXECUTION_WAVES.md real, "
            "gerado pelo Step 4 do pipeline.\n"
            "Execute primeiro:\n"
            '  llc run --step 4 --task "Planejamento do projeto"\n\n'
            "Isso gerara EXECUTION_WAVES.md com as ondas e PRPs definidos."
        )
        return []

    content = filepath.read_text(encoding="utf-8")
    clean = _strip_placeholders(content)
    lines = clean.split("\n")

    wave_headings = _find_wave_headings(content)
    if not wave_headings:
        logger.warning(
            f"Nenhuma wave heading encontrada em {filepath}.\n"
            "Certifique-se de que o arquivo segue o formato:\n"
            "  ### Onda 1: Nome da Onda\n\n"
            "O template (com `{N}` placeholders) nao e parseavel. "
            "Execute o Step 4 para gerar o arquivo real."
        )
        return []

    waves: list[WaveInfo] = []
    for idx, (hdr_start, _, name, num) in enumerate(wave_headings):
        # Range: deste heading até o próximo (ou final)
        next_start = (
            wave_headings[idx + 1][0] if idx + 1 < len(wave_headings) else len(lines)
        )
        section = "\n".join(lines[hdr_start:next_start])

        # Extrai PRP IDs do corpo da seção
        prp_ids = set()
        # Pattern: PRP-NNN
        for m in re.finditer(r"\b(PRP-\d{3,})\b", section):
            prp_ids.add(m.group(1))
        # Pattern: F0.1, F0.2 (IDs alfanuméricos usados em templates)
        for m in re.finditer(r"\b(F\d+\.\d+)\b", section):
            prp_ids.add(m.group(1))

        waves.append(WaveInfo(number=num, name=name, prps=sorted(prp_ids)))

    waves.sort(key=lambda w: w.number)
    return waves


def _find_prp_headings(content: str) -> list[tuple[int, str, str, int]]:
    """Encontra headings `#### PRP-NNN: ID — Name` no TASKS.md.

    Retorna (line_index, prp_id, name, next_heading_line).
    """
    results = []
    lines = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"####\s+(PRP-\d{3,})\s*:\s*(\S+)\s*(?:—\s*(.*))?", line.strip())
        if m:
            prp_id = m.group(1)
            full_name = f"{m.group(2)} — {m.group(3)}" if m.group(3) else m.group(2)
            results.append((i, prp_id, full_name, 0))

    # Fill next_heading
    for idx in range(len(results)):
        if idx + 1 < len(results):
            results[idx] = (
                results[idx][0],
                results[idx][1],
                results[idx][2],
                results[idx + 1][0],
            )
        else:
            results[idx] = (
                results[idx][0],
                results[idx][1],
                results[idx][2],
                len(lines),
            )

    return results


def _find_tasks_in_section(section: str) -> list[str]:
    """Encontra IDs de tarefas no corpo de uma seção.

    Busca: checkboxes `- [ ] ...` com IDs entre parenteses,
    e linhas de tabela com IDs na primeira coluna.
    """
    task_ids: set[str] = set()

    # Checkboxes: - [ ] descricao (FDN-001) ou - [x] descricao (FDN-001)
    # So captura se estiver numa linha de checkbox, nao em texto explicativo solto.
    for m in re.finditer(
        r"^[\s]*[-*\d.]+[\s]*\[[ x]\]\s*.*?\(([A-Z]+-\d+(?:\.\d+)?)\)",
        section,
        re.MULTILINE,
    ):
        task_ids.add(m.group(1))

    # Tabelas: | FDN-001 | Tarefa | Skill | ...
    for line in section.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells and re.match(r"^[A-Z]+-\d+(?:\.\d+)?$", cells[0]):
            task_ids.add(cells[0])

    return sorted(task_ids)


def parse_tasks(filepath: Path = TASKS_FILE) -> dict[str, PrpInfo]:
    """Parse TASKS.md e retorna mapping PRP → PrpInfo.

    Extrai PRPs de headings `#### PRP-NNN: ...` e tasks
    de checkboxes/tabelas no corpo de cada seção.

    Também retorna tarefas de fundação (secão 3) e segurança (seção 4)
    como pseudo-PRPs (PRP-FDN, PRP-SEC).
    """
    if not filepath.exists():
        logger.warning(f"Arquivo nao encontrado: {filepath}")
        return {}

    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    # 1. Parse PRP headings (#### PRP-NNN: ...)
    prp_headings = _find_prp_headings(content)
    prps: dict[str, PrpInfo] = {}

    for line_idx, prp_id, name, next_idx in prp_headings:
        section = "\n".join(lines[line_idx:next_idx])
        tasks = _find_tasks_in_section(section)
        prps[prp_id] = PrpInfo(prp_id=prp_id, name=name, tasks=tasks)

    # 2. Parse foundation tasks (seção 3, tables) — usa set pra evitar duplicatas
    #    Mapeia tarefas FDN/SEC/DSG como PRP-FOUNDATION, PRP-SECURITY
    section_tables: list[tuple[str, str]] = [
        ("PRP-FOUNDATION", "Foundation"),
        ("PRP-SECURITY", "Security Gates"),
    ]

    for prp_id, name in section_tables:
        if prp_id not in prps:
            prps[prp_id] = PrpInfo(prp_id=prp_id, name=name, tasks=[])

    # Find section 3 tasks (FDN-*, DSG-*) — garante unicidade com set
    fdn_tasks: set[str] = set()
    sec_tasks: set[str] = set()
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 2:
            cell0 = cells[0]
            # Foundation tasks
            if re.match(r"^FDN-\d+", cell0):
                fdn_tasks.add(cell0)
            elif re.match(r"^DSG-\d+", cell0):
                fdn_tasks.add(cell0)
            # Security tasks
            elif re.match(r"^SEC-\d+", cell0):
                sec_tasks.add(cell0)

    # Mescla com tasks já encontradas via PRP headings (evita duplicata)
    if "PRP-FOUNDATION" in prps:
        existing = set(prps["PRP-FOUNDATION"].tasks)
        prps["PRP-FOUNDATION"].tasks = sorted(existing | fdn_tasks)
    if "PRP-SECURITY" in prps:
        existing = set(prps["PRP-SECURITY"].tasks)
        prps["PRP-SECURITY"].tasks = sorted(existing | sec_tasks)

    return prps


# ── Display ──


def format_wave_list(waves: list[WaveInfo], prps: dict[str, PrpInfo]) -> str:
    """Formata lista de waves para exibicao."""
    if not waves:
        return "Nenhuma wave encontrada."

    lines = []
    for w in waves:
        prp_count = len(w.prps)
        task_count = sum(len(prps.get(p, PrpInfo(p)).tasks) for p in w.prps)
        lines.append(f"\n{'=' * 60}")
        lines.append(f"  Onda {w.number}: {w.name or '(sem nome)'}")
        lines.append(f"{'=' * 60}")
        lines.append(f"  PRPs: {prp_count}  |  Tasks: {task_count}")
        lines.append("")

        if w.prps:
            for prp_id in w.prps:
                info = prps.get(prp_id, PrpInfo(prp_id))
                name_part = f" — {info.name}" if info.name else ""
                task_part = f" ({len(info.tasks)} tasks)" if info.tasks else ""
                lines.append(f"    {prp_id}{name_part}{task_part}")
                for tid in info.tasks:
                    lines.append(f"      └── {tid}")
        else:
            lines.append("    (nenhum PRP identificado)")

    return "\n".join(lines)


# ── Pré/Pós-onda validation ──

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

    # Import consistency check logic for stub detection
    try:
        import sys

        sys.path.insert(0, str(Path.cwd() / ".ace" / "scripts"))
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "consistency_check",
            Path.cwd() / ".ace" / "scripts" / "consistency-check.py",
        )
        if spec and spec.loader:
            cc = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cc)
            is_stub_service = cc.is_stub_service
        else:
            is_stub_service = None
    except Exception as e:
        logger.warning(f"   ⚠️  Não foi possível carregar consistency-check: {e}")
        is_stub_service = None

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

    # ── Pré/Pós-onda validation ──
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

    result = subprocess.run(
        ["bash", str(PRE_WAVE_CHECK_SCRIPT), "--build-only", "--timeout", "30"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.stdout:
        for line in result.stdout.split("\n"):
            if line.strip():
                logger.info(f"   {line.strip()}")

    if result.returncode == 0:
        logger.info("✅ Pre-Wave Check: baseline OK")
        return True
    else:
        logger.error(f"❌ Pre-Wave Check FALHOU (exit: {result.returncode})")
        logger.error(f"   Corrija os erros de compilacao antes de iniciar a onda.")
        return False


def _post_wave_check(
    dry_run: bool = False, wave_num: int = 0, prp_ids: Optional[list[str]] = None
):
    def _post_wave_check(
        dry_run: bool = False, wave_num: int = 0, prp_ids: Optional[list[str]] = None
    ) -> bool:
        """Executa validacao pos-onda: build + bootstrap + health check + consistency + aceite de PRP.

        Retorna True se passou; retorna False se prp_verify encontrar CRITICAL
        (bloqueia a onda). build/bootstrap/health e consistency-check permanecem
        advisory (warnings).
        """
        if not PRE_WAVE_CHECK_SCRIPT.exists():
            logger.info(
                "ℹ️  pre-wave-check.sh nao encontrado — pulando validacao pos-onda."
            )
            return True

        if dry_run:
            logger.info("   [dry-run] post-wave-check seria executado")
            return True

        logger.info(f"\n{'─' * 50}")
        logger.info("🔍 Post-Wave Check — validando integridade apos a onda")

        result = subprocess.run(
            ["bash", str(PRE_WAVE_CHECK_SCRIPT), "--timeout", "30"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.stdout:
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

        # ── Verificação de consistência TASKS.md × código ──
        consistency_script = Path(".ace") / "scripts" / "consistency-check.py"
        if consistency_script.exists():
            logger.info(f"\n{'─' * 50}")
            logger.info("📋 Verificando consistencia TASKS.md × codigo...")
            result_cc = subprocess.run(
                ["python3", str(consistency_script)],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )
            if result_cc.stdout:
                for line in result_cc.stdout.split("\n"):
                    if line.strip() and not line.startswith("="):
                        logger.info(f"   {line.strip()}")
            if result_cc.returncode != 0 and result_cc.stderr:
                for line in result_cc.stderr.strip().split("\n"):
                    logger.warning(f"   {line.strip()}")
            else:
                logger.info("✅ Consistencia OK — documentacao reflete o codigo.")
        else:
            logger.info(
                "ℹ️  consistency-check.py nao encontrado — pulando verificacao de consistencia."
            )

        # ── Aceite mecânico de PRP (Step 11.2) — BLOQUEANTE em CRITICAL ──
        # Diferente do build/consistency (advisory), o prp_verify bloqueia a onda.
        if os.environ.get("LLC_PRP_NO_VERIFY") == "1":
            logger.info("ℹ️  prp_verify bypassado via LLC_PRP_NO_VERIFY=1.")
            return True

        verify_script = Path(".ace") / "scripts" / "prp_verify.py"
        if prp_ids and verify_script.exists():
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


# ── Execution ──


def run_wave(
    wave_num: int,
    aggregate: bool = False,
    dry_run: bool = False,
    no_worktree: bool = False,
    auto_approve: bool = False,
) -> bool:
    """Executa uma onda: itera PRPs e abre sessoes.

    Retorna True se todas as sessoes foram bem-sucedidas.
    """
    waves = parse_execution_waves()
    if not waves:
        logger.error("Nenhuma wave encontrada em EXECUTION_WAVES.md.")
        return False

    wave = next((w for w in waves if w.number == wave_num), None)
    if not wave:
        valid = [w.number for w in waves]
        logger.error(f"Wave {wave_num} nao encontrada. Waves disponiveis: {valid}")
        return False

    prps_map = parse_tasks()
    prp_ids = wave.prps if wave.prps else list(prps_map.keys())

    if not prp_ids:
        logger.warning(
            f"Wave {wave_num} nao tem PRPs associados. "
            f"Popule EXECUTION_WAVES.md ou crie PRPs no Step 3."
        )
        return False

    logger.info(f"🚀 Wave {wave_num}: {wave.name or '(sem nome)'}")
    logger.info(f"   PRPs: {len(prp_ids)}")

    if dry_run:
        logger.info("🏁 Modo dry-run — nenhuma sessao sera criada.")
        for prp_id in prp_ids:
            info = prps_map.get(prp_id, PrpInfo(prp_id))
            task_info = f" ({len(info.tasks)} tasks)" if info.tasks else ""
            logger.info(f"   • {prp_id}{task_info}")
            for tid in info.tasks:
                logger.info(f"       ├── {tid}")
        return True

    # Pre-wave validation: build + bootstrap + health (baseline)
    if not _pre_wave_check(dry_run=dry_run, wave_num=wave_num):
        logger.error(
            f"⛔ Wave {wave_num} — pre-wave check FALHOU. Corrija os erros e tente novamente."
        )
        return False

    # Import harness functions only when not dry-run
    try:
        from llc_harness import gate_check, session_end, step_run
    except ImportError as e:
        logger.error(
            f"Erro ao importar llc_harness: {e}\n\n"
            "O comando `wave run` depende dos modulos de orquestracao do harness.\n"
            "Certifique-se de estar executando a partir de .ace/scripts/:\n"
            f"  cd .ace/scripts && python llc.py wave run --wave {wave_num}"
        )
        return False

    if aggregate:
        # Sessao agregada — um unico ciclo para toda a wave
        task_desc = f"Wave {wave_num}: {wave.name or ''}. PRPs: {', '.join(prp_ids)}"
        logger.info(f"📦 Sessao agregada: {task_desc}")

        sid = step_run("11", task=task_desc, wave=wave_num, no_worktree=no_worktree)
        decision = gate_check("11", None, auto_approve=auto_approve)
        session_end(sid, decision, None, step="11")

        if decision != "approved":
            logger.warning(f"⛔ Wave {wave_num} — gate rejeitado.")
            return False
    else:
        # Sessao por PRP — um ciclo para cada PRP
        logger.info(f"📦 Sessoes individuais por PRP ({len(prp_ids)} PRPs)")

        for prp_id in prp_ids:
            info = prps_map.get(prp_id, PrpInfo(prp_id))
            task_desc = f"{prp_id}: {info.name or prp_id}"

            logger.info(f"\n{'─' * 50}")
            logger.info(f"▶  Iniciando {prp_id}")

            # API-first enforcement: verifica contratos de backend antes de PRPs com UI (Trilha B)
            if _is_ui_prp(prp_id, info):
                logger.info(f"   🎨 {prp_id} detectado como Trilha B (UI)")
                if not _verify_backend_contracts(prp_id, info, dry_run=dry_run):
                    logger.error(
                        f"⛔ {prp_id} — contratos de backend não prontos (API-first)."
                    )
                    if auto_approve:
                        logger.info("   Continuando para próximo PRP (auto-approve).")
                    else:
                        logger.info(
                            "   Wave pausada. Implemente os contratos de backend primeiro."
                        )
                        return False

            sid = step_run(
                "11", prp=prp_id, task=task_desc, wave=wave_num, no_worktree=no_worktree
            )
            decision = gate_check("11", None, auto_approve=auto_approve)
            session_end(sid, decision, None, step="11")

            if decision != "approved":
                logger.warning(f"⛔ {prp_id} — gate rejeitado.")
                if auto_approve:
                    logger.info("   Continuando para proximo PRP (auto-approve).")
                else:
                    logger.info(
                        "   Wave pausada. Execute manualmente os PRPs restantes."
                    )
                    return False

    # Post-wave validation: build + bootstrap + health (integridade) + aceite de PRP
    if not _post_wave_check(dry_run=dry_run, wave_num=wave_num, prp_ids=prp_ids):
        logger.error(f"⛔ Wave {wave_num} — pós-onda bloqueada (prp_verify CRITICAL).")
        return False

    logger.info(f"✅ Wave {wave_num} concluida.")
    return True
