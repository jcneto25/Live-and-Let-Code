#!/usr/bin/env python3
"""
prp_verify — verificação mecânica de aceite de PRP (Step 11.2 do LLC).

Lê o documento do PRP como **fonte da verdade** do que deve existir e cruza com
o código real. Nunca passa silenciosamente: um PRP com RFs na §2 mas sem código
gera um CRITICAL por RF sem evidência.

O que verifica (por PRP):
  §2  Requisitos Funcionais  — cada RF tem arquivo(s) de teste/impl declarados?
        (colunas "Teste(s)" / "Arquivo(s) impl"); arquivos ausentes ou stub ⇒ CRITICAL.
  §5  API Contracts           — cada endpoint declarado existe no código? (WARN até calibrar)
  §6  Component Spec          — cada componente (Localização) e cada estado (teste) existem?
  §9  Test Strategy           — cada arquivo de teste declarado existe e NÃO é stub-test?
  service stub                — arquivos de impl declarados não são stub (return [], TODO, ...)

Severidade:
  CRITICAL — bloqueia (exit 2 em --strict): arquivo declarado ausente/stub,
             componente/estado declarado ausente.
  WARN     — nunca bloqueia: stub-test detectado, PRP legado sem colunas de
             rastreabilidade, endpoint não localizado (pré-calibração), RF sem evidência.

Uso:
    python .ace/scripts/prp_verify.py --prp PRP-001
    python .ace/scripts/prp_verify.py --prp PRP-001 --strict   # exit 2 se CRITICAL
    python .ace/scripts/prp_verify.py --prp PRP-001 --json
    python .ace/scripts/prp_verify.py --all

Reutiliza detect_language / is_stub_file / STUB_PATTERNS / read_config de
consistency-check.py (carregado via importlib — o módulo tem hífen no nome).
"""

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

PRP_DIR = Path("docs/prps")
ARCHITECTURE_FILE = Path("docs/architecture/ARCHITECTURE.md")

CRITICAL = "CRITICAL"
WARN = "WARN"

# Raízes onde procurar arquivos declarados (bounded — nunca node_modules/.ace).
SEARCH_ROOTS = ["apps", "src", "packages", "."]
EXCLUDE_PARTS = {"node_modules", ".ace", "dist", ".git", "build", ".next",
                 "coverage", ".turbo", "target"}


# ── Carrega consistency-check.py (nome com hífen → importlib) ──

def _load_consistency_check():
    cc_path = Path(__file__).resolve().parent / "consistency-check.py"
    if not cc_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("consistency_check", cc_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CC = _load_consistency_check()
detect_language = _CC.detect_language if _CC else (lambda p: "any")
is_stub_file = _CC.is_stub_file if _CC else (lambda p, c: False)
STUB_PATTERNS = _CC.STUB_PATTERNS if _CC else {}
read_config = _CC.read_config if _CC else (lambda: {
    "prp_services": {}, "skip_task_patterns": [], "stub_patterns": {}})


def is_stub_by_pattern(file_path: str, config: dict) -> bool:
    """Stub por PADRÃO POSITIVO apenas (return [], TODO, NotImplementedError, ...).

    Diferente de consistency-check.is_stub_file, NÃO usa o critério "≤3 linhas
    significativas" — este é um gate BLOQUEANTE (CRITICAL), então compact code real
    não pode ser falsamente marcado. Exige um sinal positivo de stub. Arquivos
    pequenos sem padrão de stub não são flagados aqui."""
    full = Path(file_path)
    if not full.exists():
        return True
    content = full.read_bytes()
    lang = detect_language(file_path)
    patterns: list[str] = []
    patterns.extend(config.get("stub_patterns", {}).get("any", STUB_PATTERNS.get("any", [])))
    patterns.extend(config.get("stub_patterns", {}).get(lang, []))
    patterns.extend(STUB_PATTERNS.get(lang, []))
    for pat in patterns:
        try:
            if re.search(pat.encode(), content, re.MULTILINE):
                return True
        except re.error:
            continue
    return False


# ── Padrões de stub-TEST (teatro de testes) — distintos dos stubs de impl ──

STUB_TEST_PATTERNS: dict[str, list[str]] = {
    "typescript": [
        r"\.toBeDefined\(\)",
        r"\.toBeNull\(\)",
        r"\.toBeTruthy\(\)",
        r"\.toBeFalsy\(\)",
        r"\.toEqual\(\s*\[\s*\]\s*\)",
        r"\.toEqual\(\s*\{\s*\}\s*\)",
    ],
    "javascript": [
        r"\.toBeDefined\(\)",
        r"\.toBeNull\(\)",
        r"\.toEqual\(\s*\[\s*\]\s*\)",
    ],
    "python": [
        r"\bassert True\b",
    ],
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    rf: str = ""           # RF-XXX.N quando aplicável
    file: str = ""


@dataclass
class VerifyResult:
    prp: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def critical(self) -> int:
        return sum(1 for f in self.findings if f.severity == CRITICAL)

    @property
    def warns(self) -> int:
        return sum(1 for f in self.findings if f.severity == WARN)

    def to_dict(self) -> dict:
        return {
            "prp": self.prp,
            "critical": self.critical,
            "warn": self.warns,
            "findings": [asdict(f) for f in self.findings],
        }


# ── Resolução de caminhos ──

def _is_excluded(p: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in p.parts)


def resolve_path(declared: str) -> Path | None:
    """Resolve um caminho declarado no PRP para um Path existente (ou None).

    Tenta o caminho literal; se não existir, busca pelo basename sob raízes
    limitadas (apps/src/packages/.), excluindo node_modules/.ace/dist. Placeholders
    com `{` (ex: `{service}.spec.ts`) não resolvem → None."""
    if not declared:
        return None
    p = declared.strip().strip('`').strip().strip('"').strip("'")
    if not p or "{" in p:
        return None

    cand = Path(p)
    if cand.exists() and not _is_excluded(cand):
        return cand

    name = Path(p).name
    if not name:
        return None
    for root in SEARCH_ROOTS:
        base = Path(root)
        if not base.exists() or not base.is_dir():
            continue
        try:
            for hit in base.glob(f"**/{name}"):
                if hit.is_file() and not _is_excluded(hit):
                    return hit
        except (OSError, PermissionError):
            continue
    return None


# ── Extração de seções do PRP ──

def _get_section(content: str, num: str) -> str:
    """Retorna o texto da seção `## num.` até o próximo `## ` header."""
    lines = content.split("\n")
    start = None
    for i, line in enumerate(lines):
        if re.match(rf'^##\s+{re.escape(num)}(?:\.|\s|\b)', line):
            start = i
            break
    if start is None:
        return ""
    out = []
    for line in lines[start + 1:]:
        if re.match(r'^##\s+', line):
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
            if (i + 1 < n and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i + 1])
                    and "-" in lines[i + 1]):
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
    parts = re.split(r'[,\n]', cell)
    out = []
    for p in parts:
        p = p.strip().strip('`').strip()
        if p and p.lower() not in ("—", "-", "n/a"):
            out.append(p)
    return out


# ── Parsers por seção ──

RF_ID_RE = re.compile(r'RF-\d{3}\.\d+')
ENDPOINT_RE = re.compile(
    r'^###\s+\d+\.\d+\s+Endpoint:\s+(GET|POST|PUT|PATCH|DELETE)\s+(\S+)',
    re.MULTILINE)
LOCALIZACAO_RE = re.compile(r'\*\*Localização:\*\*\s*`([^`]+)`')


def parse_rf_table(section2: str):
    """Parser da §2. Retorna (rows, has_traceability).

    rows: lista de {id, testes: [...], impl: [...]}
    has_traceability: True se a tabela tem colunas Teste(s)/Arquivo(s) impl."""
    for header_map, data in _all_tables(section2):
        if "id" not in header_map:
            continue
        # Detecta colunas de rastreabilidade (tolerante a "Teste(s)"/"Testes"/"Impl")
        test_key = next((k for k in header_map if k.startswith("teste")), None)
        impl_key = next((k for k in header_map
                         if "impl" in k or "arquivo" in k and "teste" not in k), None)
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
    if re.search(r'N/A\s*[—-]', section5, re.IGNORECASE) and not ENDPOINT_RE.search(section5):
        return []
    return [(m.group(1), m.group(2)) for m in ENDPOINT_RE.finditer(section5)]


def parse_components(section6: str):
    """Parser da §6. Retorna [(localizacao_path, [state_test_files]), ...]."""
    if re.search(r'N/A\s*[—-]', section6, re.IGNORECASE) and not LOCALIZACAO_RE.search(section6):
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
            file_key = next((k for k in header_map if "arquivo" in k and "teste" in k), None)
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


# ── Detecção de stub-TEST ──

def is_stub_test_file(path: Path) -> tuple[bool, str]:
    """Heurística conservadora de teatro de testes.

    Flag apenas se: há blocos de teste (it/test/def test_) mas NENHUMA asserção
    real — só asserções triviais (toBeDefined/toBeNull/toEqual([])/assert True).
    Retorna (é_stub, motivo)."""
    if not path.exists() or not path.is_file():
        return False, ""
    lang = detect_language(str(path))
    patterns = STUB_TEST_PATTERNS.get(lang, [])
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False, ""

    # Conta blocos de teste
    if lang in ("typescript", "javascript"):
        test_blocks = len(re.findall(r'\b(?:it|test)\s*\(', content))
        real_asserts = len(re.findall(r'\bexpect\s*\(', content))
    elif lang == "python":
        test_blocks = len(re.findall(r'\bdef\s+test_\w+', content))
        real_asserts = len(re.findall(r'\bassert\s+', content))
    else:
        return False, ""  # não medimos outras langs por ora

    if test_blocks == 0:
        return False, ""

    trivial = 0
    for pat in patterns:
        trivial += len(re.findall(pat, content))
    real_asserts_real = max(0, real_asserts - trivial)

    if trivial > 0 and real_asserts_real == 0:
        return True, (f"{test_blocks} bloco(s) de teste, {trivial} asserção(ões) trivial(is) "
                      f"(toBeDefined/toEqual([])/...) e nenhuma asserção real")
    return False, ""


# ── Checkers ──

def check_rf_evidence(rows, has_trace, section9_files, result):
    """CRITICAL se arquivo declarado ausente/stub; WARN se RF sem evidência ou teste fora do §9."""
    if not rows:
        return
    if not has_trace:
        for r in rows:
            result.findings.append(Finding(
                WARN, "rf_legacy_no_traceability",
                f"{r['id']}: PRP legado sem colunas de rastreabilidade (Teste(s)/Arquivo(s) impl) "
                f"— verifique manualmente a implementação", rf=r["id"]))
        return

    section9_set = set(section9_files)
    for r in rows:
        declared = r["testes"] + r["impl"]
        if not declared:
            result.findings.append(Finding(
                WARN, "rf_no_evidence",
                f"{r['id']}: sem arquivos de teste/impl declarados — não verificável mecanicamente",
                rf=r["id"]))
            continue
        for decl in declared:
            resolved = resolve_path(decl)
            if resolved is None:
                result.findings.append(Finding(
                    CRITICAL, "rf_file_missing",
                    f"{r['id']}: arquivo declarado ausente: {decl}", rf=r["id"], file=decl))
            else:
                # stub de impl (não de teste) ⇒ CRITICAL (padrão positivo apenas)
                if not _looks_like_test(decl) and is_stub_by_pattern(str(resolved), read_config()):
                    result.findings.append(Finding(
                        CRITICAL, "rf_file_stub",
                        f"{r['id']}: arquivo declarado é stub: {decl}", rf=r["id"], file=decl))
        for tp in r["testes"]:
            if tp not in section9_set and resolve_path(tp):
                result.findings.append(Finding(
                    WARN, "rf_test_not_in_section9",
                    f"{r['id']}: teste {tp} não está listado na §9 do PRP", rf=r["id"], file=tp))


def _looks_like_test(path: str) -> bool:
    name = Path(path).name.lower()
    return (".spec." in name or ".test." in name or name.startswith("test_")
            or "_test." in name)


def check_tests(section9_files, result):
    """CRITICAL se arquivo de teste declarado ausente; WARN se for stub-test."""
    for decl in section9_files:
        resolved = resolve_path(decl)
        if resolved is None:
            result.findings.append(Finding(
                CRITICAL, "test_file_missing",
                f"arquivo de teste da §9 ausente: {decl}", file=decl))
            continue
        is_stub, reason = is_stub_test_file(resolved)
        if is_stub:
            result.findings.append(Finding(
                WARN, "stub_test",
                f"possível teatro de testes em {decl}: {reason}", file=decl))


def check_components(comps, result):
    """CRITICAL se Localização ausente ou teste de estado ausente."""
    for path, state_tests in comps:
        resolved = resolve_path(path)
        if resolved is None:
            result.findings.append(Finding(
                CRITICAL, "component_missing",
                f"componente declarado (Localização) ausente: {path}", file=path))
        for st in state_tests:
            if resolve_path(st) is None:
                result.findings.append(Finding(
                    CRITICAL, "component_state_test_missing",
                    f"teste de estado do componente ausente: {st} (Localização: {path})",
                    file=st))


def check_endpoints(endpoints, result):
    """WARN-only até calibração per-stack: procura a rota no código sob apps/src."""
    if not endpoints:
        return
    haystack = _collect_code_text()
    if not haystack:
        return  # sem código para cruzar — não emite WARN falso
    for method, route in endpoints:
        if _route_found(route, haystack):
            continue
        result.findings.append(Finding(
            WARN, "endpoint_not_found",
            f"endpoint declarado não localizado no código (pré-calibração): "
            f"{method} {route}"))


def _collect_code_text() -> str:
    """Concatena código-fonte sob apps/src/packages para busca de rotas (bounded)."""
    chunks = []
    for root in ("apps", "src", "packages"):
        base = Path(root)
        if not base.exists():
            continue
        for hit in base.rglob("*"):
            if not hit.is_file() or _is_excluded(hit):
                continue
            if hit.suffix not in (".ts", ".tsx", ".js", ".jsx", ".py", ".go"):
                continue
            try:
                chunks.append(hit.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if sum(len(c) for c in chunks) > 2_000_000:  # teto de 2 MB
                break
    return "\n".join(chunks)


def _route_found(route: str, haystack: str) -> bool:
    """Normaliza parâmetros de rota e procura o prefixo no código."""
    norm = re.sub(r':\w+|{\w+}|\[\w+\]', '', route).rstrip('/')
    if not norm:
        return True
    # procura o path (ou sufixo dele) como literal
    return norm in haystack


# ── Orquestração por PRP ──

def verify_prp(prp_path: Path) -> VerifyResult:
    result = VerifyResult(prp=prp_path.stem)
    content = prp_path.read_text(encoding="utf-8", errors="replace")

    section2 = _get_section(content, "2")
    section5 = _get_section(content, "5")
    section6 = _get_section(content, "6")
    section9 = _get_section(content, "9")

    rf_rows, has_trace = parse_rf_table(section2)
    endpoints = parse_endpoints(section5)
    comps = parse_components(section6)
    section9_files = parse_test_files(section9)

    check_rf_evidence(rf_rows, has_trace, section9_files, result)
    check_tests(section9_files, result)
    check_components(comps, result)
    check_endpoints(endpoints, result)

    return result


def discover_prps() -> list[Path]:
    if not PRP_DIR.exists():
        return []
    out = []
    for p in sorted(PRP_DIR.glob("PRP-*.md")):
        if re.match(r'PRP-\d', p.name):
            out.append(p)
    return out


def resolve_prp_path(prp_id: str) -> Path | None:
    """Aceita 'PRP-001' ou caminho completo."""
    cand = Path(prp_id)
    if cand.exists():
        return cand
    # PRP-001 → docs/prps/PRP-001*.md
    hits = sorted(PRP_DIR.glob(f"{prp_id}*.md"))
    hits = [h for h in hits if re.match(r'PRP-\d', h.name)]
    return hits[0] if hits else None


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(
        description="Verificação mecânica de aceite de PRP (Step 11.2 do LLC)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--prp", help="ID do PRP (ex: PRP-001) ou caminho")
    g.add_argument("--all", action="store_true", help="Verifica todos os PRP-*.md")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 2 se houver CRITICAL")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    args = parser.parse_args()

    if args.all:
        prps = discover_prps()
        if not prps:
            msg = "Nenhum PRP encontrado em docs/prps/ (apenas PRP_TEMPLATE.md)."
            if args.json:
                print(json.dumps({"prps": [], "critical": 0, "warn": 0}, ensure_ascii=False))
            else:
                print(f"ℹ️  {msg}")
            return 0
    else:
        path = resolve_prp_path(args.prp)
        if path is None:
            print(f"❌ PRP não encontrado: {args.prp}", file=sys.stderr)
            return 1
        prps = [path]

    results = [verify_prp(p) for p in prps]
    total_critical = sum(r.critical for r in results)
    total_warn = sum(r.warns for r in results)

    if args.json:
        print(json.dumps({
            "prps": [r.to_dict() for r in results],
            "critical": total_critical,
            "warn": total_warn,
        }, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"\n{'=' * 60}")
            print(f"📋 {r.prp} — {r.critical} CRITICAL, {r.warns} WARN")
            print(f"{'=' * 60}")
            if not r.findings:
                print("✅ Nenhuma pendência encontrada.")
            for f in r.findings:
                glyph = "⛔" if f.severity == CRITICAL else "⚠️ "
                rf = f" [{f.rf}]" if f.rf else ""
                fl = f" ({f.file})" if f.file else ""
                print(f"  {glyph} {f.severity} {f.code}{rf}{fl}")
                print(f"      {f.message}")
        print(f"\n{'=' * 60}")
        print(f"Total: {total_critical} CRITICAL, {total_warn} WARN "
              f"({len(results)} PRP(s))")
        print(f"{'=' * 60}")

    if args.strict and total_critical > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
