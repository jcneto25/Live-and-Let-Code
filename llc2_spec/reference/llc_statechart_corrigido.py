"""[DEPRECADO COMO RUNTIME — Passagem 4, decisao D-A]

Este arquivo e mantido APENAS como documentacao executavel do nivel macro.
A autoridade de transicao e `contracts.py::TRANSITIONS` (NodeMachine por no).
O chart abaixo foi rebaixado a PROJECAO DERIVADA: veja
`macro_projection.py` (funcao pura `macro_view(configs)`) e
`macro_projection.divergences()`.

Motivos: (1) dois statecharts = duas autoridades de transicao, proibido por
P1 §3.5 e P2 §0.3; (2) contem estados sem origem no registry
(`discovery.use_cases`, `self_heal`, `deployed`); (3) exigiria a dependencia
`python-statemachine >= 3.2`, ausente no ambiente.

Requer `python-statemachine` para executar; nao e parte do runtime LLC 2.0.

--------------------------------------------------------------------------
""" + """Statechart de orquestracao do LLC — versao corrigida e executavel.

Correcoes em relacao a proposta anterior:
  1. todo estado e alcancavel (senao InvalidDefinition na definicao da classe);
  2. confianca e POR PERGUNTA; Noul nao tem confidence -> usa |2p - 1|;
  3. Score devolve o INDICE DO NIVEL (0..n-1) + legend, nao "nota 1..5";
  4. tres faixas de confianca (alta/media/baixa), nao duas;
  5. retries e estado da maquina, incrementado por ACTION (guard nao tem side effect);
  6. gate humano lembra a origem (gate_id) em vez de voltar sempre ao mesmo estado;
  7. regiao paralela com filhos final=True para disparar done.state.
"""

from __future__ import annotations

import json
from pathlib import Path

from statemachine import State, StateChart

REPLAY_LOG = Path(".ace/logs/replay.jsonl")


def noul_confidence(p: float) -> float:
    """Noul nao retorna confidence; a distancia de 0.5 e o mesmo eixo do Choice."""
    return abs(2 * p - 1)


class LLCPipeline(StateChart):
    """Nucleo deterministico: o agente propoe, a maquina dispoe."""

    # --- estado mutavel da maquina (persistivel junto do artefato) ---
    retries = 0
    max_retries = 3
    gate_id: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replay: list[dict] = []

    # ------------------------------------------------------------------
    # MACRO 1 — DESCOBERTA E ESPECIFICACAO (steps 0.5 .. 2.5)
    # ------------------------------------------------------------------
    class discovery(State.Compound):
        ingestion = State("Ingestion", initial=True)
        vision = State("Vision + Modules")
        use_cases = State("Casos de Uso")
        specs = State("7 Specs")
        prd_generation = State("PRDs", final=True)

        to_vision = ingestion.to(vision)
        to_use_cases = vision.to(use_cases)
        to_specs = use_cases.to(specs)
        to_prd = specs.to(prd_generation)

    # ------------------------------------------------------------------
    # MACRO 2 — PLANEJAMENTO E ARQUITETURA (steps 3 .. 6)
    # ------------------------------------------------------------------
    class planning(State.Compound):
        prp_generation = State("PRPs", initial=True)
        planning_waves = State("Planning")
        architecture = State("Architecture + ADRs")
        tasks = State("Tasks", final=True)

        to_waves = prp_generation.to(planning_waves)
        to_architecture = planning_waves.to(architecture)
        to_tasks = architecture.to(tasks)

    # ------------------------------------------------------------------
    # MACRO 3 — IMPLEMENTACAO (steps 8 .. 10): regiao PARALELA de qualidade
    # ------------------------------------------------------------------
    class implementation(State.Compound):
        coding = State("Coding Agent", initial=True)

        class quality_gates(State.Parallel):
            # ids DEVEM ser unicos entre regioes, senao done.state nao dispara
            class fitness(State.Compound):
                fitness_running = State("fitness-functions.py", initial=True)
                fitness_ok = State("41 checks OK", final=True)

                fitness_pass = fitness_running.to(fitness_ok)

            class coverage(State.Compound):
                coverage_running = State("gate 10.8", initial=True)
                coverage_ok = State("cobertura OK", final=True)

                coverage_pass = coverage_running.to(coverage_ok)

        verified = State("Implementacao verificada", final=True)

        start_coding = coding.to(quality_gates)
        # done.state so dispara quando TODAS as regioes chegam a final
        done_state_quality_gates = quality_gates.to(verified)

    # ------------------------------------------------------------------
    # ESTADOS DE GOVERNANCA
    # ------------------------------------------------------------------
    human_gate = State("Human Validation Gate")
    self_heal = State("Auto-refactor")
    deployed = State("Deploy", final=True)
    blocked = State("Bloqueado", final=True)

    # ------------------------------------------------------------------
    # TRANSICOES AVALIADAS PELO JEV (guardas puras)
    # ------------------------------------------------------------------
    eval_artifact = (
        discovery.prd_generation.to(
            planning.prp_generation, cond="approved_and_confident"
        )
        | discovery.prd_generation.to(self_heal, cond="can_self_heal")
        | discovery.prd_generation.to(human_gate, on="open_gate")
    )

    eval_adr = (
        planning.tasks.to(implementation.coding, cond="approved_and_confident")
        | planning.tasks.to(self_heal, cond="can_self_heal")
        | planning.tasks.to(human_gate, on="open_gate")
    )

    rework = self_heal.to(discovery.prd_generation, on="increment_retries")

    # o gate humano volta para a ORIGEM correta
    human_approve_prd = human_gate.to(
        discovery.prd_generation, cond="gate_is_prd", on="close_gate"
    )
    human_approve_plan = human_gate.to(
        planning.prp_generation, cond="gate_is_plan", on="close_gate"
    )
    human_reject = human_gate.to(blocked, on="close_gate")

    deploy = implementation.verified.to(deployed, on="close_gate")

    # ------------------------------------------------------------------
    # GUARDAS PURAS — sem side effects, testaveis sem Jev e sem rede
    # ------------------------------------------------------------------
    def _answers(self, jev):
        return (jev or {}).get("answers", {})

    def _min_confidence(self, jev) -> float:
        """Menor confianca entre as perguntas; Noul entra via |2p-1|."""
        confs = []
        for a in self._answers(jev).values():
            if a.get("type") == "noul":
                confs.append(noul_confidence(a.get("noul", 0.5)))
            else:
                confs.append(a.get("confidence", 0.0))
        return min(confs) if confs else 0.0

    def _quality_ok(self, jev) -> bool:
        """Score = indice do nivel (0..n-1). Nivel 3 de 0..4 = 'bom'."""
        prd = self._answers(jev).get("prd_quality", {})
        risk = self._answers(jev).get("security_risk", {})
        return (
            prd.get("score", 0) >= 3
            and risk.get("noul", 1.0) <= 0.05
        )

    def approved_and_confident(self, jev=None, **kwargs) -> bool:
        return self._quality_ok(jev) and self._min_confidence(jev) >= 0.85

    def can_self_heal(self, jev=None, **kwargs) -> bool:
        """Faixa media: reformula sozinho, mas so ate max_retries."""
        return self._min_confidence(jev) >= 0.50 and self.retries < self.max_retries

    def gate_is_prd(self, **kwargs) -> bool:
        return self.gate_id == "prd"

    def gate_is_plan(self, **kwargs) -> bool:
        return self.gate_id == "plan"

    # ------------------------------------------------------------------
    # ACTIONS — aqui ficam os side effects
    # ------------------------------------------------------------------
    def increment_retries(self, **kwargs):
        self.retries += 1

    def open_gate(self, jev=None, step: str = "", **kwargs):
        self.gate_id = "prd" if step.startswith("discovery") else "plan"
        self._log(step, jev, approved=False)

    def close_gate(self, jev=None, step: str = "", **kwargs):
        self.retries = 0
        self.gate_id = None
        self._log(step, jev, approved=True)

    def _log(self, step, jev, approved: bool):
        """Decision Signature — base do Deterministic Replay."""
        entry = {
            "step": step,
            "jev": jev,
            "min_confidence": round(self._min_confidence(jev), 4),
            "approved": approved,
            "configuration": sorted(self.configuration_values),
        }
        self.replay.append(entry)
        return entry


# ----------------------------------------------------------------------
# Execucao de verificacao
# ----------------------------------------------------------------------
def _jev(score=4, score_conf=0.95, risk=0.01):
    return {
        "answers": {
            "prd_quality": {"type": "score", "score": score, "confidence": score_conf},
            "security_risk": {"type": "noul", "noul": risk},
        }
    }


if __name__ == "__main__":
    # A) caminho feliz: confianca alta -> avanca sem humano
    sm = LLCPipeline()
    for e in ("to_vision", "to_use_cases", "to_specs", "to_prd"):
        sm.send(e)
    sm.send("eval_artifact", jev=_jev(), step="discovery.prd_generation")
    print("A) aprovado  ->", sorted(sm.configuration_values))

    # B) nota ruim, confianca alta: auto-refactor, e retries incrementa
    sm = LLCPipeline()
    for e in ("to_vision", "to_use_cases", "to_specs", "to_prd"):
        sm.send(e)
    for i in range(4):
        sm.send("eval_artifact", jev=_jev(score=1), step="discovery.prd_generation")
        print(f"B) tentativa {i+1} ->", sorted(sm.configuration_values), "retries:", sm.retries)
        if "self_heal" in sm.configuration_values:
            sm.send("rework")
    print("   retries acumulados:", sm.retries)

    # C) faixa media (0.60): reformula (nao mata o pipeline)
    sm = LLCPipeline()
    for e in ("to_vision", "to_use_cases", "to_specs", "to_prd"):
        sm.send(e)
    sm.send("eval_artifact", jev=_jev(score=4, score_conf=0.60), step="discovery.prd_generation")
    print("C) faixa media ->", sorted(sm.configuration_values))

    # D) faixa baixa: vai para o humano e lembra a origem
    sm = LLCPipeline()
    for e in ("to_vision", "to_use_cases", "to_specs", "to_prd"):
        sm.send(e)
    sm.send("eval_artifact", jev=_jev(score=1, score_conf=0.20), step="discovery.prd_generation")
    print("D) faixa baixa ->", sorted(sm.configuration_values), "gate:", sm.gate_id)
    sm.send("human_approve_prd", step="human_gate")
    print("   apos humano ->", sorted(sm.configuration_values))

    # E) regiao paralela so avanca quando as duas fecham
    sm = LLCPipeline()
    for e in ("to_vision", "to_use_cases", "to_specs", "to_prd"):
        sm.send(e)
    sm.send("eval_artifact", jev=_jev(), step="discovery.prd_generation")
    for e in ("to_waves", "to_architecture", "to_tasks"):
        sm.send(e)
    sm.send("eval_adr", jev=_jev(), step="planning.tasks")
    sm.send("start_coding")
    sm.send("fitness_pass")
    print("E) so fitness ->", sorted(sm.configuration_values))
    sm.send("coverage_pass")
    print("   + coverage ->", sorted(sm.configuration_values))
    sm.send("deploy", step="implementation.verified")
    print("   deploy     ->", sorted(sm.configuration_values))

    # F) Decision Signature
    print("F) replay:", json.dumps(sm.replay, ensure_ascii=False)[:200], "...")
