"""LLC 2.0 — Capability Control (Phase 5).

Responsabilidades:
1. Gerar perfis de permissão do cliente por estado (ex.: `.claude/settings.local.json`)
2. `DefaultToolBroker` — broker in-process sobre a matriz declarativa (contrato p/ SDK futuro)
3. Integração com `NodeMachine` para atualização automática de permissões em transições
4. Verificação post-hoc via diff + zonas 🔴 (rede de segurança, não prevenção)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import (
    CAPABILITY_MATRIX,
    FORBIDDEN_EVERYWHERE,
    DefaultToolBroker,
    ToolBroker,
    capabilities_for_state,
    Event,
    EventType,
    NodeMachine,
)


# ══════════════════════════════════════════════════════════════════════════
# 1. Mapeamento de capabilities → tool calls do cliente
# ══════════════════════════════════════════════════════════════════════════

# Mapeia capabilities internas para tool calls conhecidos do cliente (ex.: Claude Code)
# O cliente de IA usa estes nomes em suas tool calls.
CAPABILITY_TO_CLIENT_TOOLS: dict[str, set[str]] = {
    "read_index": {"Read", "Glob", "Grep", "LS"},
    "read_artifacts": {"Read", "Glob", "Grep"},
    "write_artifacts": {"Write", "Edit", "MultiEdit"},
    "run_tests": {"Bash"},  # pytest, etc.
    "git_commit": {"Bash"},  # git commit
    "build_decision_state": {"Read", "Write"},  # construcao de contexto
    "jev_eval": {"Bash"},  # invocao Jev via CLI
    "run_hard_eval": {"Bash"},  # pytest, lint, typecheck
    "apply_policy": {"Read", "Write"},  # decisao de politica
    "apply_changes": {"Write", "Edit", "MultiEdit"},
    "rollback": {"Bash"},  # git restore/reset
    "show_evidence": {"Read"},
    "request_approval": {"Bash"},  # interacao humana
}


# Mapeia capabilities proibidas globalmente para tool calls do cliente
FORBIDDEN_TO_CLIENT_TOOLS: dict[str, set[str]] = {
    "deploy": {"Bash"},       # deploy em producao
    "force_push": {"Bash"},   # git push --force
    "delete_session": {"Bash"},  # rm -rf .ace/sessions
}


# ── Vocabulário de tools por cliente (F5/5.1) ────────────────────────────────
# Tradução dos nomes canônicos (estilo Claude Code, exatos) para a convenção
# de cada cliente. `claude-code`/`generic` são identidade; os demais são
# BEST-EFFORT (convenção pública, não certificados contra os clientes —
# ver docs/architecture/capability-control.md §5). Cliente desconhecido usa
# o mapa `generic` (vocabulário canônico). Os três mapas best-effort
# compartilham a constante abaixo — ao certificar um cliente, desdobre o
# mapa próprio (split on divergence).
_LOWERCASE_TOOL_ALIASES: dict[str, str] = {
    "Read": "read", "Glob": "glob", "Grep": "grep", "LS": "list",
    "Write": "write", "Edit": "edit", "MultiEdit": "edit", "Bash": "bash",
}
_CLIENT_TOOL_ALIASES: dict[str, dict[str, str]] = {
    "claude-code": {},
    "generic": {},
    "opencode": _LOWERCASE_TOOL_ALIASES,
    "codex": _LOWERCASE_TOOL_ALIASES,
    "cursor": _LOWERCASE_TOOL_ALIASES,
}

SUPPORTED_CLIENTS: frozenset[str] = frozenset(_CLIENT_TOOL_ALIASES)


def _translate_tools(tools: set[str], client: str) -> set[str]:
    """Traduz tool calls canônicos para o vocabulário do cliente."""
    aliases = _CLIENT_TOOL_ALIASES.get(client)
    if aliases is None:
        return set(tools)
    return {aliases.get(tool, tool) for tool in tools}


# Ids do detector (`llc_harness.replay.detect_agent_client`) → ids de mapa.
_DETECTED_TO_CLIENT = {
    "claude": "claude-code",
    "opencode": "opencode",
    "codex": "codex",
    "cursor": "cursor",
}


def normalize_client_id(detected: str | None) -> str:
    """Normaliza o id detectado para um id com mapa; resto → "generic"."""
    if not detected:
        return "generic"
    return _DETECTED_TO_CLIENT.get(detected.strip().lower(), "generic")


def profile_path_for_client(client: str) -> Path:
    """Destino do perfil: settings nativo (claude) ou advisory .llc2/."""
    if client == "claude-code":
        return Path(".claude/settings.local.json")
    return Path(".llc2/permissions") / f"{client}.json"


# ══════════════════════════════════════════════════════════════════════════
# 2. Perfil de permissão do cliente (ex.: .claude/settings.local.json)
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ClientPermissionProfile:
    """Perfil de permissão para um cliente de IA específico.

    Gera arquivos como `.claude/settings.local.json` que o cliente respeita.
    """
    client: str  # ex.: "claude-code", "cursor", "windsurf"
    allowed_tools: frozenset[str]
    denied_tools: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_claude_settings(self) -> dict[str, Any]:
        """Gera formato `.claude/settings.local.json`."""
        return {
            "permissions": {
                "allow": sorted(self.allowed_tools),
                "deny": sorted(self.denied_tools),
            },
            "metadata": dict(self.metadata),
        }

    def write(self, path: Path) -> None:
        """Escreve o perfil no caminho especificado.

        Zona config 🔴: nunca destrói sem backup. Arquivo existente com
        conteúdo diferente é preservado em `<nome>.bak` (último backup);
        reescrita idêntica é no-op (sem churn, sem backup).
        """
        if self.client == "claude-code":
            payload = self.to_claude_settings()
        else:
            # Formato genérico JSON (inclui client="generic" ou outro)
            payload = {
                "client": self.client,
                "allowed": sorted(self.allowed_tools),
                "denied": sorted(self.denied_tools),
                "metadata": dict(self.metadata),
            }
        content = json.dumps(payload, indent=2)
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == content:
                return
            path.with_name(path.name + ".bak").write_text(
                existing, encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _capabilities_to_client_tools(
    capabilities: frozenset[str],
    client: str = "claude-code",
) -> set[str]:
    """Converte capabilities internas para tool calls do cliente."""
    tools: set[str] = set()
    for cap in capabilities:
        tools.update(CAPABILITY_TO_CLIENT_TOOLS.get(cap, set()))
    # Remove ferramentas de capabilities proibidas APENAS se estiverem no conjunto permitido
    # (FORBIDDEN_EVERYWHERE capabilities não estão no CAPABILITY_MATRIX, então isso
    # é uma salvaguarda caso alguma capacidade proibida vazou para o conjunto permitido)
    for forbidden in FORBIDDEN_EVERYWHERE:
        if forbidden in capabilities:
            tools.difference_update(FORBIDDEN_TO_CLIENT_TOOLS.get(forbidden, set()))
    return _translate_tools(tools, client)


def generate_permission_profile(
    state_id: str,
    client: str = "claude-code",
    metadata: Mapping[str, Any] | None = None,
) -> ClientPermissionProfile:
    """Gera perfil de permissão para um estado específico e cliente."""
    caps = capabilities_for_state(state_id)
    vocab = client if client in SUPPORTED_CLIENTS else "generic"
    allowed = _capabilities_to_client_tools(caps, vocab)

    # Ferramentas negadas: apenas as de capabilities proibidas que de alguma forma
    # vazaram para o conjunto permitido (salvaguarda)
    denied: set[str] = set()
    for forbidden in FORBIDDEN_EVERYWHERE:
        if forbidden in caps:
            denied.update(FORBIDDEN_TO_CLIENT_TOOLS.get(forbidden, set()))
    denied = _translate_tools(denied, vocab)

    meta = dict(metadata) if metadata else {
        "state_id": state_id, "generated_by": "llc2.capabilities"}
    meta.setdefault("client_map", vocab)
    return ClientPermissionProfile(
        client=client,
        allowed_tools=frozenset(allowed),
        denied_tools=frozenset(denied),
        metadata=meta,
    )


# ══════════════════════════════════════════════════════════════════════════
# 3. Gerenciador de permissões integrado ao NodeMachine
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class CapabilityManager:
    """Gerencia permissões do cliente sincronizadas com o NodeMachine.

    Uso típico:
        manager = CapabilityManager(machine, client="claude-code")
        manager.sync()  # atualiza .claude/settings.local.json para o estado atual
    """
    machine: NodeMachine
    client: str = "claude-code"
    profile_path: Path = profile_path_for_client("claude-code")
    _last_state: str = field(default="", init=False)

    def sync(self, metadata: Mapping[str, Any] | None = None) -> ClientPermissionProfile:
        """Sincroniza permissões com o estado atual da máquina."""
        config = self.machine.configuration()
        state_id = config["configuration"]

        if state_id == self._last_state:
            # Sem mudança de estado, não reescreve
            return generate_permission_profile(state_id, self.client, metadata)

        profile = generate_permission_profile(state_id, self.client, metadata)
        profile.write(self.profile_path)
        self._last_state = state_id
        return profile

    def get_current_profile(self) -> ClientPermissionProfile:
        """Retorna o perfil do estado atual sem escrever."""
        config = self.machine.configuration()
        state_id = config["configuration"]
        return generate_permission_profile(state_id, self.client)


# ══════════════════════════════════════════════════════════════════════════
# 4. ToolBroker aprimorado com auditoria
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class AuditingToolBroker:
    """ToolBroker que registra tentativas de uso de ferramentas (auditoria).

    Trabalha com tool calls do cliente (ex.: "Read", "Write", "Bash").
    Usado para detecção post-hoc (opção 3 do documento).
    """
    audit_log: list[dict[str, Any]] = field(default_factory=list, init=False)

    def authorize(self, state_id: str, tool: str) -> bool:
        """Verifica se tool call do cliente é permitido no estado."""
        try:
            allowed_caps = capabilities_for_state(state_id)
            allowed_tools = _capabilities_to_client_tools(allowed_caps)
            allowed = tool in allowed_tools
        except KeyError:
            allowed = False
        self.audit_log.append({
            "state_id": state_id,
            "tool": tool,
            "allowed": allowed,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })
        return allowed

    def get_audit_log(self) -> list[dict[str, Any]]:
        return list(self.audit_log)

    def clear_audit_log(self) -> None:
        self.audit_log.clear()


# ══════════════════════════════════════════════════════════════════════════
# 5. Verificação post-hoc (opção 3): diff + zonas
# ══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PostHocViolation:
    """Violação detectada post-hoc."""
    file_path: str
    tool_used: str
    state_at_time: str
    capability_required: str
    zone: str  # "red", "yellow", "green"


def detect_capability_violations(
    machine: NodeMachine,
    diff_files: Sequence[str],
    tool_calls: Sequence[tuple[str, str]],  # (tool, file_path)
    zone_map: Mapping[str, str],  # file_path -> zone
) -> list[PostHocViolation]:
    """Detecta violações de capacidade comparando tool calls com a matriz do estado.

    Args:
        machine: NodeMachine para consultar capacidades por estado
        diff_files: Arquivos modificados no commit/diff
        tool_calls: Lista de (tool_name, file_path) executados
        zone_map: Mapeamento arquivo -> zona (red/yellow/green)

    Returns:
        Lista de violações detectadas.
    """
    violations: list[PostHocViolation] = []
    config = machine.configuration()
    state_id = config["configuration"]

    try:
        allowed_caps = capabilities_for_state(state_id)
        allowed_tools = _capabilities_to_client_tools(allowed_caps)
    except KeyError:
        # Estado sem matriz — não pode verificar
        return violations

    # Mapeia tool call para capability necessária (aproximação)
    tool_to_capability: dict[str, str] = {}
    for cap, tools in CAPABILITY_TO_CLIENT_TOOLS.items():
        for tool in tools:
            if tool not in tool_to_capability:
                tool_to_capability[tool] = cap

    for tool, file_path in tool_calls:
        if tool not in allowed_tools:
            capability = tool_to_capability.get(tool, "unknown")
            zone = zone_map.get(file_path, "unknown")
            violations.append(PostHocViolation(
                file_path=file_path,
                tool_used=tool,
                state_at_time=state_id,
                capability_required=capability,
                zone=zone,
            ))

    return violations


def detect_modified_file_violations(
    diff_files: Sequence[str],
    *,
    machine: NodeMachine | None = None,
    state_id: str | None = None,
    is_red_zone: Any | None = None,
) -> list[PostHocViolation]:
    """Rede pós-agente (F5/5.3): sinaliza modificações em zona 🔴.

    Não observa tool calls (invisíveis para subprocess — limitação
    documentada em docs/architecture/capability-control.md): baseia-se
    em diff + zonas. `is_red_zone` injetável (testes); default importa
    `llc_replay.zones` tardiamente (evita ciclo de import).
    """
    if not diff_files:
        return []
    red_check = is_red_zone
    if red_check is None:
        try:
            from llc_replay.zones import is_red_zone as _red
        except ImportError:
            return []
        red_check = _red
    try:
        state = (machine.configuration()["configuration"]
                 if machine is not None else (state_id or "unknown"))
    except Exception:
        state = "unknown"
    violations: list[PostHocViolation] = []
    for file_path in diff_files:
        try:
            is_red = bool(red_check(file_path))
        except Exception:
            continue
        if is_red:
            violations.append(PostHocViolation(
                file_path=str(file_path),
                tool_used="unobserved",
                state_at_time=str(state),
                capability_required="write_artifacts",
                zone="red",
            ))
    return violations


# ══════════════════════════════════════════════════════════════════════════
# 6. Hook de integração com NodeMachine
# ══════════════════════════════════════════════════════════════════════════

def install_capability_hooks(
    machine: NodeMachine,
    manager: CapabilityManager,
    broker: AuditingToolBroker | None = None,
) -> None:
    """Instala hooks no NodeMachine para sincronização automática de permissões.

    Nota: NodeMachine não tem sistema de hooks nativo. Esta função é um
    placeholder para quando houver suporte a callbacks em transições.
    Atualmente, a sincronização deve ser chamada explicitamente:
        manager.sync()
    """
    # Placeholder para futura expansão
    pass


# ══════════════════════════════════════════════════════════════════════════
# 7. CLI helper
# ══════════════════════════════════════════════════════════════════════════

def write_permission_profile_for_state(
    state_id: str,
    output: Path | None = None,
    client: str = "claude-code",
) -> Path:
    """Helper CLI: escreve perfil de permissão para um estado específico."""
    # Para arquivos .json genéricos, usa formato genérico (client=generic)
    # Para .claude/settings.local.json, usa formato claude
    effective_client = client
    if output and output.name == "settings.local.json" and "claude" in str(output):
        effective_client = "claude-code"
    elif output and output.suffix == ".json" and client == "claude-code":
        effective_client = "generic"
    
    profile = generate_permission_profile(state_id, effective_client)
    target = output or Path(f".llc2/permissions/{state_id}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    profile.write(target)
    return target


__all__ = [
    "CAPABILITY_TO_CLIENT_TOOLS",
    "FORBIDDEN_TO_CLIENT_TOOLS",
    "SUPPORTED_CLIENTS",
    "ClientPermissionProfile",
    "generate_permission_profile",
    "normalize_client_id",
    "profile_path_for_client",
    "CapabilityManager",
    "AuditingToolBroker",
    "PostHocViolation",
    "detect_capability_violations",
    "detect_modified_file_violations",
    "install_capability_hooks",
    "write_permission_profile_for_state",
]