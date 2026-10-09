"""LLC 2.0 — LLM-as-Jev Transport (shim para Fase 1).

Quando o serviço Jev real não está disponível, este transport usa o LLM
subprocess existente (claude, opencode, codex, cursor) para emular as
primitivas Jev (Choice, Score, Noul).

O prompt é estruturado em JSON (nunca XML) para eliminar erros de parsing.
A resposta é validada e convertida para JevRawResponse, permitindo que o
JevAdapter opere sem modificações.

Este shim é provisório: quando o Jev real for integrado, basta substituir
o transport no JevAdapter.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any

from llc2.jev_adapter import JevRawResponse, JevRequest, SemanticUnavailable


def _detect_llm_client() -> str | None:
    for client in ["claude", "opencode", "codex", "cursor"]:
        if shutil.which(client):
            return client
    return None


def _build_shim_prompt(request: JevRequest) -> str:
    """Monta prompt JSON a partir das perguntas do question set."""
    lines: list[str] = [
        "Você é um classificador semântico deterministico. Responda APENAS com JSON válido.",
        "",
        f"Modelo esperado: {request.model}",
        f"Question set: {request.question_set_id} v{request.question_set_version}",
        "",
        "Para cada pergunta abaixo, preencha o campo correspondente no JSON de resposta.",
        "",
    ]
    for name, spec in request.questions.items():
        kind = spec["type"]
        instructions = spec.get("instructions", "")
        criteria = spec.get("criteria")
        lines.append(f"--- {name} ({kind}) ---")
        lines.append(f"Instrucoes: {instructions}")
        if kind == "choice" and criteria:
            lines.append("Opcoes:")
            for opt, desc in criteria.items():
                lines.append(f"  {opt}: {desc}")
            lines.append("Resposta: {{'choice': '<opcao>', 'probabilities': {{'<opcao>': 0.XX, ...}}, 'confidence': 0.XX}}")
        elif kind == "score" and criteria:
            lines.append("Niveis:")
            for i, lvl in enumerate(criteria):
                lines.append(f"  {i}: {lvl}")
            lines.append("Resposta: {{'score': <indice>, 'probabilities': {{'<indice>': 0.XX, ...}}, 'confidence': 0.XX}}")
        elif kind == "noul":
            lines.append("Resposta: {{'noul': 0.XX}}  (probabilidade de verdadeiro, 0.0 a 1.0)")
        lines.append("")

    lines.extend([
        "Responda com UM único objeto JSON contendo TODAS as respostas:",
        "{",
    ])
    for name in request.questions:
        lines.append(f'  "{name}": {{...}},')
    lines[-1] = lines[-1].rstrip(",")
    lines.extend(["}", ""])
    lines.append("Não inclua markdown, explicações ou código fora do JSON.")
    return "\n".join(lines)


def _extract_json_block(text: str) -> str:
    """Extrai bloco JSON de markdown ou texto cru."""
    # Tenta bloco markdown ```json ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Tenta objeto JSON cru (primeiro { ... } balanceado)
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def _parse_answer(name: str, kind: str, raw: Any) -> dict[str, Any]:
    """Normaliza resposta bruta para o formato JevRawResponse.answers."""
    if kind == "choice":
        choice = raw.get("choice") if isinstance(raw, dict) else None
        probs = raw.get("probabilities") if isinstance(raw, dict) else {}
        conf = raw.get("confidence") if isinstance(raw, dict) else None
        if choice is None or conf is None:
            raise SemanticUnavailable(f"{name}: choice ou confidence ausente")
        return {"choice": choice, "probabilities": dict(probs), "confidence": float(conf)}

    if kind == "score":
        score = raw.get("score") if isinstance(raw, dict) else None
        probs = raw.get("probabilities") if isinstance(raw, dict) else {}
        conf = raw.get("confidence") if isinstance(raw, dict) else None
        if score is None or conf is None:
            raise SemanticUnavailable(f"{name}: score ou confidence ausente")
        return {"score": int(score), "probabilities": dict(probs), "confidence": float(conf)}

    if kind == "noul":
        p = raw.get("noul") if isinstance(raw, dict) else None
        if p is None:
            # Tenta p_true como alias
            p = raw.get("p_true") if isinstance(raw, dict) else None
        if p is None:
            raise SemanticUnavailable(f"{name}: noul ou p_true ausente")
        return {"noul": float(p)}

    raise SemanticUnavailable(f"{name}: tipo desconhecido '{kind}'")


class LlmAsJevTransport:
    """Transport Jev que usa LLM subprocess como backend.

    Não é mock: é um shim operacional que permite que a Fase 1 funcione
    sem infraestrutura Jev real.
    """

    def __init__(self, client: str | None = None, timeout_s: int | None = None) -> None:
        self.client = client or _detect_llm_client()
        # Lê timeout da policy quando não explicitado (F1)
        if timeout_s is None:
            try:
                from llc2.contracts import load_policy
                policy = load_policy()
                timeout_s = policy.limits.get("jev_timeout_s", 30)
            except Exception:
                timeout_s = 30
        self.timeout_s = timeout_s

    def call(self, request: JevRequest) -> JevRawResponse:
        if not self.client:
            raise SemanticUnavailable("nenhum cliente LLM disponível no PATH")

        prompt = _build_shim_prompt(request)
        try:
            # Usa STDIN (compatível com todos os CLIs) — não --prompt
            process = subprocess.Popen(
                [self.client],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output, _ = process.communicate(input=prompt, timeout=self.timeout_s)
        except Exception as exc:
            raise SemanticUnavailable(f"LLM subprocess falhou: {exc}") from exc

        json_text = _extract_json_block(output)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise SemanticUnavailable(
                f"LLM retornou JSON inválido: {exc}\n--- raw ---\n{output[:500]}"
            ) from exc

        answers: dict[str, Any] = {}
        for name, spec in request.questions.items():
            raw = payload.get(name)
            if raw is None:
                continue
            try:
                answers[name] = _parse_answer(name, spec["type"], raw)
            except SemanticUnavailable:
                # resposta parcial não é fatal — a Policy rebaixa um nível
                continue

        if not answers:
            raise SemanticUnavailable("LLM retornou zero respostas válidas")

        return JevRawResponse(
            model=request.model,
            request_id=f"llm-shim-{request.question_set_id}",
            answers=answers,
            usage={"input_tokens": len(prompt) // 4, "output_tokens": len(json_text) // 4},
        )
