#!/usr/bin/env python3
"""Parsing and display for EXECUTION_WAVES.md and TASKS.md."""

import logging
import re
from pathlib import Path

from .models import PrpInfo, WaveInfo

logger = logging.getLogger(__name__)

EXECUTION_WAVES_FILE = Path("docs/planning/EXECUTION_WAVES.md")
TASKS_FILE = Path("docs/planning/TASKS.md")


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
        # Pattern: PRP-NNN e PRP-<trilha>-<versão> (ex: PRP-001, PRP-WIZARD-1A,
        # PRP-GRAPH-2B). O padrão antigo `PRP-\d{3,}` não capturava os IDs
        # reais do pipeline (PRP-WIZARD-1A etc.) — fix P3 (PRP-WIZARD-2.0).
        # O fecho `[A-Za-z0-9]` (não obrigatório) evita capturar pontuação
        # final ("PRP-WIZARD-1A." → "PRP-WIZARD-1A") — fix review P3.
        for m in re.finditer(
            r"\b(PRP-[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?)\b",
            section,
        ):
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


def parse_tasks(filepath: Path | None = None) -> dict[str, PrpInfo]:
    """Extrai PRPs de headings `#### PRP-NNN: ...` e tasks
    de checkboxes/tabelas no corpo de cada seção.

    Também retorna tarefas de fundação (secão 3) e segurança (seção 4)
    como pseudo-PRPs (PRP-FDN, PRP-SEC).

    `filepath` é resolvido em call-time (não def-time): um `None` lê o
    `TASKS_FILE` atual do módulo, permitindo monkeypatch em testes.
    """
    if filepath is None:
        filepath = TASKS_FILE
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


def build_step_wave_map(sessions: list[dict], waves: list[WaveInfo]) -> dict[str, int]:
    """Mapeia step_id → número da onda (PRP-WIZARD-2.0 swimlanes).

    Ponte entre duas fontes existentes:
    - `sessions` (index.json): cada sessão liga `llc_step_id` a um `prp`
    - `waves` (EXECUTION_WAVES.md): cada onda lista seus PRPs (`wave.prps`)

    Um step pertence à onda que contém o PRP da sua sessão. Steps sem sessão,
    sem `prp`, ou cujo PRP não esteja em nenhuma onda ficam FORA do mapa — o
    Kanban os agrupa na swimlane "Sem onda". Função pura (sem I/O).

    Determinismo (fix review P3): um step pode ter várias sessões com PRPs de
    ondas diferentes (ex: step 10.8 rodou sob EVALS-F2 e EVALS-F5). Vence a
    sessão MAIS RECENTE por `timestamp`/`completed_at` — independe da ordem
    de iteração do arquivo, que é uma convenção, não um contrato.
    """
    prp_to_wave = {prp: w.number for w in waves for prp in w.prps}
    mapping: dict[str, int] = {}

    def _ts(s: dict) -> str:
        return s.get("timestamp") or s.get("completed_at") or ""

    for s in sorted(sessions, key=_ts):  # ascendente → a mais recente vence
        step_id = s.get("llc_step_id")
        prp = s.get("prp")
        if not step_id or not prp:
            continue
        wave_n = prp_to_wave.get(prp)
        if wave_n is not None:
            mapping[step_id] = wave_n
    return mapping


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
