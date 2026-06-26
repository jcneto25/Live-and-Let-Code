#!/usr/bin/env python3
"""
Verifica consistência entre o estado declarado no TASKS.md e o código real.

Lê o mapeamento PRP→serviços do .ace/consistency-config.yaml (gerado a partir da
seção 6.5 do ARCHITECTURE.md). Para cada PRP marcado como concluído no TASKS.md,
verifica se os arquivos de serviço correspondentes têm implementação real (não são stub).

Uso:
    python .ace/scripts/consistency-check.py
    python .ace/scripts/consistency-check.py --json
    python .ace/scripts/consistency-check.py --strict   # exit 1 se divergência
    python .ace/scripts/consistency-check.py --update-config  # gera config inicial do ARCHITECTURE.md

Linguagens suportadas para detecção de stub:
    TypeScript, JavaScript, Python, Go, Rust, Ruby, Java, PHP, Elixir, C#, Kotlin
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ACE_DIR = Path(".ace")
CONFIG_FILE = ACE_DIR / "consistency-config.yaml"
TASKS_FILE = Path("docs/planning/TASKS.md")
ARCHITECTURE_FILE = Path("docs/architecture/ARCHITECTURE.md")


# ── Padrões de stub multi-linguagem ──

STUB_PATTERNS: dict[str, list[str]] = {
    "any": [
        r"TODO",
        r"FIXME",
        r"NotImplementedError",
        r"NotImplementedException",
        r"not implemented",
        r"unimplemented",
        r"\* stub \*/",
        r"// stub",
        r"return Promise\.resolve\(\[\]\)",
        r"return Promise\.resolve\(\{\}\)",
        r"return Promise\.reject",
    ],
    "typescript": [
        r"return\s*\[\s*\]",
        r"return\s*\{\s*\}",
        r"return null as any",
    ],
    "javascript": [
        r"return\s*\[\s*\]",
        r"return\s*\{\s*\}",
    ],
    "python": [
        r"raise NotImplementedError",
        r"return\s*\[\s*\]",
        r"return\s*\{\s*\}",
        r"^\s*pass\s*$",
    ],
    "go": [
        r"return nil, nil",
        r"todo!\(\)",
        r"return\s*\[\s*\]",
    ],
    "rust": [
        r"todo!\(\)",
        r"unimplemented!\(\)",
        r"Vec::new\(\)",
        r"return vec!\[\]",
    ],
    "ruby": [
        r"raise NotImplementedError",
        r"return\s*\[\s*\]",
    ],
    "java": [
        r"throw new UnsupportedOperationException",
        r"throw new RuntimeException\(.*not implemented",
        r"return null;",
    ],
    "php": [
        r"throw new \w+Exception\(.*not implemented",
        r"return\s*\[\s*\]",
    ],
    "elixir": [
        r"raise \"not implemented",
        r"defimpl.*, for:.* do$",
    ],
    "csharp": [
        r"throw new NotImplementedException",
        r"throw new NotSupportedException",
    ],
    "kotlin": [
        r"TODO\(\)",
        r"throw NotImplementedError",
    ],
}


def detect_language(file_path: str) -> str:
    """Detecta linguagem baseada na extensão do arquivo."""
    ext_map = {
        ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript",
        ".py": "python",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".java": "java",
        ".php": "php",
        ".ex": "elixir", ".exs": "elixir",
        ".cs": "csharp",
        ".kt": "kotlin", ".kts": "kotlin",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "any")


def read_config() -> dict:
    """Lê o .ace/consistency-config.yaml. Retorna dict vazio se não existir."""
    default = {
        "prp_services": {},
        "skip_task_patterns": [],
        "stub_patterns": {},
    }
    if not CONFIG_FILE.exists():
        return default
    if yaml is None:
        print("ERRO: PyYAML não instalado. Execute: pip install pyyaml", file=sys.stderr)
        sys.exit(2)
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
        if data is None:
            return default
        for key in default:
            data.setdefault(key, default[key])
        return data
    except (yaml.YAMLError, OSError) as e:
        print(f"ERRO ao ler {CONFIG_FILE}: {e}", file=sys.stderr)
        sys.exit(2)


def extract_completed_prps(tasks_file: Path, config: dict) -> dict[str, list[dict]]:
    """Extrai tarefas concluídas do TASKS.md.

    Retorna {prp_id: [{"id": str, "desc": str}]} para tarefas não ignoradas
    pelos padrões de skip do config.
    """
    if not tasks_file.exists():
        return {}

    content = tasks_file.read_text(encoding="utf-8")
    skip_patterns = [re.compile(p, re.IGNORECASE) for p in config.get("skip_task_patterns", [])]
    result: dict[str, list[dict]] = {}
    current_prp = "transversal"

    # Procura por IDs de PRP no formato PRP-NNN e referências a PRP-NNN
    for line in content.split("\n"):
        prp_match = re.search(r"(PRP-\d{3})", line)
        if prp_match:
            current_prp = prp_match.group(1)
            result.setdefault(current_prp, [])

        # Tarefa marcada como concluída: procura por ✅ em linhas de task
        task_id_match = re.match(
            r"\|\s*([\w-]+)\s*\|([^|]*)\|.*\|\s*✅\s*\|", line
        )
        if task_id_match:
            task_id = task_id_match.group(1)
            task_desc = task_id_match.group(2).strip()

            # Pula tarefas que correspondem aos padrões de skip (UI, testes, etc.)
            if any(p.search(task_desc) for p in skip_patterns):
                continue

            result.setdefault(current_prp, [])
            result[current_prp].append({"id": task_id, "desc": task_desc})

    return result


def is_stub_file(file_path: str, config: dict) -> bool:
    """Verifica se um arquivo parece ser stub (implementação vazia/não finalizada).

    Critérios (qualquer um caracteriza como stub):
    1. Arquivo não existe
    2. Arquivo tem poucas linhas significativas (≤ 3)
    3. Arquivo contém padrões de stub detectados
    """
    full_path = Path.cwd() / file_path

    if not full_path.exists():
        return True  # não existe = stub (não implementado)

    content = full_path.read_bytes()

    # Critério 2: poucas linhas significativas
    lines = content.split(b"\n")
    significant = [
        l for l in lines
        if l.strip()
        and not l.strip().startswith(b"import ")
        and not l.strip().startswith(b"from ")
        and not l.strip().startswith(b"use ")
        and not l.strip().startswith(b"package ")
        and not l.strip().startswith(b"# ")
        and not l.strip().startswith(b"// ")
        and not l.strip().startswith(b"/*")
        and not l.strip().startswith(b"*")
        and not l.strip().startswith(b"@")
        and not l.strip().startswith(b"}")
        and not l.strip().startswith(b"```")
    ]
    if len(significant) <= 3:
        return True

    # Critério 3: padrões de stub
    lang = detect_language(file_path)
    patterns: list[str] = []

    # Padrões universais
    patterns.extend(config.get("stub_patterns", {}).get("any", STUB_PATTERNS.get("any", [])))

    # Padrões por linguagem do config
    patterns.extend(config.get("stub_patterns", {}).get(lang, []))

    # Padrões por linguagem dos defaults
    patterns.extend(STUB_PATTERNS.get(lang, []))

    for pattern in patterns:
        try:
            if re.search(pattern.encode(), content, re.MULTILINE):
                return True
        except re.error:
            continue  # ignora padrão inválido

    return False


def architecture_to_config(arch_file: Path) -> dict:
    """Extrai configuração de consistência da seção 6.5 do ARCHITECTURE.md.

    Interpreta o bloco YAML dentro da seção. Se não encontrar, retorna vazio.
    """
    if not arch_file.exists():
        print(f"ℹ️  {arch_file} não encontrado — use --update-config manual")
        return {}

    content = arch_file.read_text(encoding="utf-8")
    # Procura pelo bloco YAML na seção 6.5
    # Formato esperado:
    #   ```yaml
    #   # .ace/consistency-config.yaml
    #   prp_services:
    #     ...
    #   ```
    yaml_match = re.search(
        r"```yaml\n(.*?)```",
        content, re.DOTALL
    )
    if not yaml_match:
        print(f"⚠️  Nenhum bloco yaml encontrado em {arch_file} (seção 6.5)")
        return {}

    if yaml is None:
        print("ERRO: PyYAML não instalado. Execute: pip install pyyaml", file=sys.stderr)
        sys.exit(2)

    try:
        data = yaml.safe_load(yaml_match.group(1))
        return data if data else {}
    except yaml.YAMLError as e:
        print(f"⚠️  Erro ao parsear YAML do ARCHITECTURE.md: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Verifica consistência entre TASKS.md e código implementado"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="Exit code 1 se houver divergência")
    parser.add_argument("--update-config", action="store_true",
                        help="Gera .ace/consistency-config.yaml a partir do ARCHITECTURE.md")
    args = parser.parse_args()

    repo_root = Path.cwd()

    # --update-config: extrai do ARCHITECTURE.md e salva
    if args.update_config:
        data = architecture_to_config(repo_root / ARCHITECTURE_FILE)
        if not data:
            # Seção vazia ou sem YAML — não gera arquivo vazio
            print("ℹ️  Nenhum mapeamento encontrado no ARCHITECTURE.md.")
            print("   Popule a seção 6.5 (Mapeamento PRP → Serviços) e re-execute.")
            sys.exit(0)

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
        print(f"✅ Configuração gerada em {CONFIG_FILE}")
        print(f"   Revise e ajuste os caminhos e padrões antes de usar.")
        sys.exit(0)

    # Modo normal: lê config e verifica
    config = read_config()

    if not config.get("prp_services"):
        # Tenta extrair do ARCHITECTURE.md automaticamente
        data = architecture_to_config(repo_root / ARCHITECTURE_FILE)
        if data and "prp_services" in data:
            config["prp_services"] = data.get("prp_services", {})
        if data and "skip_task_patterns" in data:
            config["skip_task_patterns"] = data.get("skip_task_patterns", [])
        if data and "stub_patterns" in data:
            config["stub_patterns"] = data.get("stub_patterns", {})

    if not config.get("prp_services"):
        print(f"{'='*60}")
        print("📋 VERIFICAÇÃO DE CONSISTÊNCIA")
        print(f"{'='*60}")
        print(f"\n⚠️  Nenhum mapeamento PRP→serviços encontrado.")
        print(f"\n   Para configurar:")
        print(f"   1. Popule a seção 6.5 no ARCHITECTURE.md com o mapeamento")
        print(f"   2. Execute: python .ace/scripts/consistency-check.py --update-config")
        print(f"   3. Revise o arquivo gerado em {CONFIG_FILE}")
        print(f"\n{'='*60}")
        sys.exit(0)

    completed = extract_completed_prps(repo_root / TASKS_FILE, config)

    issues = []
    stats = {"prps_analyzed": 0, "services_stub": 0, "services_ok": 0, "divergences": 0}

    for prp, services in sorted(config["prp_services"].items()):
        prp_tasks = completed.get(prp, [])
        if not prp_tasks:
            continue  # PRP sem tarefas concluídas — não verificar

        stats["prps_analyzed"] += 1

        for service_path in services:
            if is_stub_file(service_path, config):
                stats["services_stub"] += 1
                stats["divergences"] += 1
                issues.append({
                    "prp": prp,
                    "service": service_path,
                    "tasks_completed": [t["id"] for t in prp_tasks],
                    "severity": "divergence",
                    "message": (
                        f"{prp}: {service_path} é stub, mas TASKS.md marca "
                        f"{', '.join(t['id'] for t in prp_tasks)} como ✅ — "
                        f"ou a tarefa não está completa ou o service precisa ser implementado."
                    ),
                })
            else:
                stats["services_ok"] += 1

    result = {
        **stats,
        "issues": issues,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("📋 VERIFICAÇÃO DE CONSISTÊNCIA — TASKS.md vs Código")
        print(f"{'='*60}")
        print(f"PRPs com tarefas concluídas analisados: {stats['prps_analyzed']}")
        print(f"Services implementados: {stats['services_ok']}")
        print(f"Services stub: {stats['services_stub']}")
        print(f"Divergências: {stats['divergences']}")

        if issues:
            print(f"\n❌ DIVERGÊNCIAS ENCONTRADAS:")
            for issue in issues:
                print(f"")
                print(f"  [{issue['prp']}] {issue['service']}")
                for t in issue['tasks_completed']:
                    print(f"         Tarefa marcada {t} como ✅ mas código é stub")
        else:
            print(f"\n✅ Nenhuma divergência — documentação reflete o código.")

        print(f"{'='*60}\n")

    if args.strict and issues:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
