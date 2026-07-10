#!/usr/bin/env python3
"""Extração de seções/tabelas e parsers por seção do PRP."""

import re


def _get_section(content: str, num: str) -> str:
    """Retorna o texto da seção `## num.` até o próximo `## ` header."""
    lines = content.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^##\s+{re.escape(num)}(?:\.|\s|\b)", line):
            start = i
            break
    if start is None:
        return ""
    out = []
    for line in lines[start + 1 :]:
        if re.match(r"^##\s+", line):
            break
        out.append(line)
    return "\n".join(out)


def _first_table(lines: list[str], start: int = 0):
    """Encontra a primeira tabela markdown a partir de `start`.

    Retorna (header_map, data_rows, next_index) ou (None, [], next_index).
    header_map = {nome_coluna_lower: índice} sobre as células de dados."""
    i = start
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        if line.startswith("|") and line.endswith("|"):
            header_cells = [c.strip() for c in line.split("|")[1:-1]]
            if (
                i + 1 < n
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1])
                and "-" in lines[i + 1]
            ):
                header_map = {c.lower(): idx for idx, c in enumerate(header_cells)}
                data = []
                j = i + 2
                while j < n:
                    dl = lines[j].rstrip()
                    if not (dl.startswith("|") and dl.endswith("|")):
                        break
                    cells = [c.strip() for c in dl.split("|")[1:-1]]
                    data.append(cells)
                    j += 1
                return header_map, data, j
        i += 1
    return None, [], n


def _all_tables(section: str):
    """Itera todas as tabelas de uma seção: yields (header_map, data_rows)."""
    lines = section.split("\n")
    idx = 0
    while idx < len(lines):
        header_map, data, idx = _first_table(lines, idx)
        if header_map is None:
            break
        yield header_map, data


def _split_paths(cell: str) -> list[str]:
    """Divide uma célula de caminhos separados por vírgula, removendo backticks."""
    if not cell:
        return []
    parts = re.split(r"[,\n]", cell)
    out = []
    for p in parts:
        p = p.strip().strip("`").strip()
        if p and p.lower() not in ("—", "-", "n/a"):
            out.append(p)
    return out


# ── Parsers por seção ──

RF_ID_RE = re.compile(r"RF-\d{3}\.\d+")
ENDPOINT_RE = re.compile(
    r"^###\s+\d+\.\d+\s+Endpoint:\s+(GET|POST|PUT|PATCH|DELETE)\s+(\S+)", re.MULTILINE
)
LOCALIZACAO_RE = re.compile(r"\*\*Localização:\*\*\s*`([^`]+)`")


def parse_rf_table(section2: str):
    """Parser da §2. Retorna (rows, has_traceability).

    rows: lista de {id, testes: [...], impl: [...]}
    has_traceability: True se a tabela tem colunas Teste(s)/Arquivo(s) impl."""
    for header_map, data in _all_tables(section2):
        if "id" not in header_map:
            continue
        # Detecta colunas de rastreabilidade (tolerante a "Teste(s)"/"Testes"/"Impl")
        test_key = next((k for k in header_map if k.startswith("teste")), None)
        impl_key = next(
            (
                k
                for k in header_map
                if "impl" in k or "arquivo" in k and "teste" not in k
            ),
            None,
        )
        has_trace = bool(test_key or impl_key)
        rows = []
        for cells in data:
            if not cells:
                continue
            rf_id_match = RF_ID_RE.search(cells[0])
            if not rf_id_match:
                continue
            rf_id = rf_id_match.group(0)
            testes = _split_paths(cells[header_map[test_key]]) if test_key else []
            impl = _split_paths(cells[header_map[impl_key]]) if impl_key else []
            rows.append({"id": rf_id, "testes": testes, "impl": impl})
        return rows, has_trace
    return [], False


def parse_endpoints(section5: str) -> list[tuple[str, str]]:
    """Parser da §5. Retorna [(method, route), ...]. [] se N/A."""
    if re.search(r"N/A\s*[—-]", section5, re.IGNORECASE) and not ENDPOINT_RE.search(
        section5
    ):
        return []
    return [(m.group(1), m.group(2)) for m in ENDPOINT_RE.finditer(section5)]


def parse_components(section6: str):
    """Parser da §6. Retorna [(localizacao_path, [state_test_files]), ...]."""
    if re.search(r"N/A\s*[—-]", section6, re.IGNORECASE) and not LOCALIZACAO_RE.search(
        section6
    ):
        return []
    comps = []
    # Cada componente: bloco entre Localização e a próxima Localização (ou fim).
    locs = list(LOCALIZACAO_RE.finditer(section6))
    for idx, m in enumerate(locs):
        path = m.group(1).strip()
        block_start = m.end()
        block_end = locs[idx + 1].start() if idx + 1 < len(locs) else len(section6)
        block = section6[block_start:block_end]
        state_tests = []
        for header_map, data in _all_tables(block):
            if "estado" not in header_map and "arquivo de teste" not in header_map:
                continue
            file_key = next(
                (k for k in header_map if "arquivo" in k and "teste" in k), None
            )
            if file_key is None:
                continue
            for cells in data:
                if len(cells) > header_map[file_key]:
                    state_tests.extend(_split_paths(cells[header_map[file_key]]))
        comps.append((path, state_tests))
    return comps


def parse_test_files(section9: str) -> list[str]:
    """Parser da §9 (9.1/9.2/9.3). Coleta a coluna 'Arquivo' de cada tabela."""
    files = []
    seen = set()
    for header_map, data in _all_tables(section9):
        file_key = next((k for k in header_map if k == "arquivo"), None)
        if file_key is None:
            continue
        for cells in data:
            if len(cells) > header_map[file_key]:
                for p in _split_paths(cells[header_map[file_key]]):
                    if p not in seen:
                        seen.add(p)
                        files.append(p)
    return files
