#!/usr/bin/env python3
"""Leitura e parsing do DELTA_REPORT.md.

Robusto a acentos (F-04): o template DELTA_REPORT_TEMPLATE.md usa
ortografia portuguesa acentuada ("Alteração", "Necessários",
"Classificação", "Iteração proposta") mas versões legadas/ASCII também
são aceitas. O parser normaliza diacriticos antes de casar.
"""

import os
import re
import unicodedata
from typing import Any

from .paths import DELTA_REPORT_PATH
from .skip import should_use_semantic_impact

# Flag de segurança (Fase 2, tarefa 2.5): default "1" (§9 do plano).
# Desligada → portão sempre True (comportamento legado, sem restrição).
IMPACT_FIRST_ENV = "LLC2_DELTA_IMPACT_FIRST"
IMPACT_FIRST_DEFAULT = "1"


def _strip_accents(text: str) -> str:
    """Remove diacriticos (acentos) para matching insensivel a acentuacao.
    NFC -> NFKD separa base + combining marks -> encode ascii descarta marks."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def delta_report_exists() -> bool:
    return DELTA_REPORT_PATH.exists()


def _impact_first_enabled() -> bool:
    """Lê a flag por chamada (nunca congela no import)."""
    return os.environ.get(IMPACT_FIRST_ENV, IMPACT_FIRST_DEFAULT).strip().lower() \
        not in ("0", "", "false", "no")


def _default_engine() -> Any | None:
    """GraphEngine sobre o grafo real; None se indisponível (conservador).

    Imports condicionais (tarefa 2.1): llc_delta nunca quebra sem llc_graph.
    """
    try:
        from llc_graph.builder import GraphBuilder
        from llc_graph.engine import GraphEngine
    except ImportError:
        return None
    try:
        return GraphEngine(GraphBuilder().build())
    except Exception:
        return None


def _resolve_engine(engine: Any | None) -> Any | None:
    """Engine injetado (testes) ou default sobre o grafo real."""
    return engine if engine is not None else _default_engine()


def affected_nodes_for_delta(
    changed_nodes: set[str] | frozenset[str],
    *,
    engine: Any | None = None,
) -> frozenset[str]:
    """União de `impact_of()` sobre as raízes da mudança (tarefa 2.2).

    Levanta KeyError em raiz desconhecida (fail fast, como o engine) —
    o portão `should_assess_step_impact` trata como conservador (True).
    Levanta RuntimeError se o engine estiver indisponível.
    """
    eng = _resolve_engine(engine)
    if eng is None:
        raise RuntimeError("GraphEngine indisponível para impact_of-first")
    affected: set[str] = set()
    for root in changed_nodes:
        affected.update(eng.impact_of(root))
    return frozenset(affected)


def should_assess_step_impact(
    step_id: str,
    changed_nodes: set[str] | frozenset[str],
    *,
    engine: Any | None = None,
) -> bool:
    """Portão impact_of-first (Fase 2 / R-4): avaliar este step semanticamente?

    - Flag desligada → True (legado: sem restrição).
    - Engine indisponível → True (conservador).
    - `changed_nodes` vazio → False (nada mudou — tarefa 2.6).
    - Raiz desconhecida (KeyError) → True (conservador — tarefa 2.2).
    - Senão → `should_use_semantic_impact(step, affected)`.

    Notas: a raiz da mudança retorna False (não está no próprio
    `impact_of`; a mudança é entrada conhecida, vai p/ execute_steps —
    sem Jev para decidir sobre ela). Steps em ALWAYS_RUN retornam True
    pela guarda fail-closed (herdada do helper). Este portão governa
    gasto semântico, nunca autoridade de skip (`is_step_skipped` segue
    sendo o único decider de skip).

    Caminho sancionado para disparar avaliação semântica de delta
    (`llc2.delta_semantic_impact`): Jev só no residual afetado.
    """
    if not _impact_first_enabled():
        return True
    if not changed_nodes:
        return False
    eng = _resolve_engine(engine)
    if eng is None:
        return True
    try:
        affected = affected_nodes_for_delta(changed_nodes, engine=eng)
    except KeyError:
        return True
    return should_use_semantic_impact(step_id, affected)


def parse_delta_report() -> dict | None:
    """Le o DELTA_REPORT.md e extrai a secao de plano de execucao.

    Retorna dict com:
      - change_type: "major" | "minor"
      - execute_steps: lista de step_ids (strings) a executar
      - skip_steps: lista de {step_id, reason, artifacts_reused}
      - iteration: string "vN" ou None
      - affected_prps: lista de PRP ids
      - new_prps: lista de PRP-N ids
    Retorna None se o arquivo nao existir ou nao for parseavel.
    """
    if not DELTA_REPORT_PATH.exists():
        return None

    content = DELTA_REPORT_PATH.read_text(encoding="utf-8")
    # Conteudo normalizado (sem acentos) para regex/substring insensivel a acento.
    norm = _strip_accents(content)

    result = {
        "change_type": "unknown",
        "execute_steps": [],
        "skip_steps": [],
        "iteration": None,
        "affected_prps": [],
        "new_prps": [],
    }

    # Extrai iteracao do §1 (casa "Iteracao proposta" e "Iteração proposta")
    # O template usa bold: | **Iteração proposta** | `v2.0` | — \** permite os **.
    m = re.search(r"Iteracao proposta\**\s*\|\s*`(v[\d.]+)`", norm)
    if m:
        result["iteration"] = m.group(1)

    # Extrai classificacao (casa "Classificacao" e "Classificação")
    m = re.search(r"Classificacao\**\s*\|\s*`(\w+)`", norm)
    if m:
        result["change_type"] = m.group(1).lower()

    # Extrai steps a executar (§5.1) — header sem acento no template
    in_execute = False
    in_skip = False
    for line in content.split("\n"):
        stripped = line.strip()

        if "Steps a Executar" in stripped:
            in_execute = True
            in_skip = False
            continue
        if "Steps a Pular" in stripped:
            in_execute = False
            in_skip = True
            # Pula o cabecalho da tabela (| Step | ... |)
            continue
        if in_execute and stripped.startswith("|") and not stripped.startswith("|---"):
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if parts and len(parts) >= 1:
                step_id = parts[0].strip()
                if step_id and not step_id.startswith("Step"):
                    result["execute_steps"].append(step_id)

        if in_skip and stripped.startswith("|") and not stripped.startswith("|---"):
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if parts and len(parts) >= 2:
                step_id = parts[0].strip()
                # Filtra linha de cabecalho "Step | Justificativa | ..." (F-05),
                # espelhando o filtro que ja existe no bloco execute_steps.
                if step_id and not step_id.lower() == "step":
                    skip_entry = {
                        "step_id": step_id,
                        "reason": parts[1].strip(),
                        "artifacts_reused": parts[2].strip() if len(parts) > 2 else "",
                    }
                    result["skip_steps"].append(skip_entry)
                    # Muda in_skip para False apos ler a linha (so espera uma linha da tabela)
                    # Na verdade, a tabela tem multiplas linhas, entao mantemos True

    # Extrai PRPs afetados (§3.2) — casa "Alteracao" e "Alteração"
    # Pattern PRP-\d evita capturar header "PRP Original" como PRP real.
    target_affected = _strip_accents("PRPs Existentes com Alteração (PRP-A)")
    in_affected = False
    for line in content.split("\n"):
        if target_affected in _strip_accents(line):
            in_affected = True
            continue
        if in_affected and line.startswith("|") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if parts and re.match(r"PRP-\d", parts[0]):
                result["affected_prps"].append(parts[0])
        elif in_affected and not line.startswith("|") and line.strip():
            in_affected = False

    # Extrai novos PRPs (§4) — casa "Necessarios" e "Necessários"
    # Pattern PRP-N-\d evita capturar header "PRP-N" como PRP real.
    target_new = _strip_accents("Novos PRPs Necessários (PRP-N)")
    in_new = False
    for line in content.split("\n"):
        if target_new in _strip_accents(line):
            in_new = True
            continue
        if in_new and line.startswith("|") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if parts and re.match(r"PRP-N-\d", parts[0]):
                result["new_prps"].append(parts[0])
        elif in_new and not line.startswith("|") and line.strip():
            in_new = False

    return result
