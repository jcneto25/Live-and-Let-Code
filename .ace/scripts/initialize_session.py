#!/usr/bin/env python3
"""
Inicializa uma nova sessão ACE no Live-and-Let-Code.

Fluxo:
1. Lê index.json para identificar sessão anterior
2. Carrega context_seed da sessão anterior (se existir)
3. Cria novo arquivo de sessão a partir do template
4. Atualiza index.json com a nova sessão
5. Retorna informações da sessão para o agente

Uso:
    python .ace/scripts/initialize_session.py --step 0.5 --task "Visao Estrategica"
    python .ace/scripts/initialize_session.py --step 5 --task "Refatoracao JWT" --project tjce-audit --wave 1
    python .ace/scripts/initialize_session.py --step 0.1 --task "Conversao Docling" --json

Worktree automático:
    Por padrao, sessoes com --prp ou steps auto_worktree (11 Execução, 11.1 OWASP)
    criam worktree isolado automaticamente. Use --no-worktree para desativar.
    python .ace/scripts/initialize_session.py --step 11 --task "PRP-001" --prp PRP-001 --wave 1
    python .ace/scripts/initialize_session.py --step 11 --task "PRP-001" --prp PRP-001 --no-worktree
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from llc_steps import normalize_step, REGISTRY

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"
TEMPLATE_FILE = ACE_DIR / "templates" / "session.template.md"

# Fonte de verdade: llc_steps.REGISTRY. LLC_STEPS/VALID_STEPS ficam como shim de
# compat (assinatura antiga {numero: nome}) — agora incluem 10.5/10.6/10.7/11.1.
LLC_STEPS = {spec.number: spec.name for spec in REGISTRY.values()}
VALID_STEPS = frozenset(LLC_STEPS.keys())


@dataclass
class SessionInfo:
    session_id: str
    file: str
    status: str
    llc_step: float
    llc_step_id: str = ""
    tags: list = field(default_factory=list)
    timestamp: str = ""


def extract_context_seed(session_file: Path) -> Optional[str]:
    if not session_file.exists():
        return None
    content = session_file.read_text(encoding='utf-8')
    match = re.search(r'<context_seed>(.*?)</context_seed>', content, re.DOTALL)
    return match.group(1).strip() if match else None


def get_next_session_id() -> str:
    """Próximo ID de sessão livre (max+1, verificado contra o disco).

    Usa max(numeros)+1 — não len+1 — para NÃO colidir quando uma sessão do meio
    é deletada (len+1 reaproveitaria um número existente e sobrescreveria).
    Mantenha em sincronia com validate-session-write.get_next_sequence.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if not SESSIONS_DIR.exists():
        return f"{today}-001"
    pattern = re.compile(rf"^{re.escape(today)}-(\d{{3}})\.md$")
    nums = []
    for f in SESSIONS_DIR.glob(f"{today}-*.md"):
        m = pattern.match(f.name)
        if m:
            nums.append(int(m.group(1)))
    next_num = (max(nums) + 1) if nums else 1
    candidate = f"{today}-{next_num:03d}"
    while (SESSIONS_DIR / f"{candidate}.md").exists():  # guard contra race/criação manual
        next_num += 1
        candidate = f"{today}-{next_num:03d}"
    return candidate


def get_previous_session() -> Optional[SessionInfo]:
    if not INDEX_FILE.exists():
        return None
    try:
        index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"index.json inválido: {e}")
        return None
    sessions = index.get("sessions", [])
    for session_data in reversed(sessions):
        if session_data.get("status") in ("completed", "in_progress"):
            return SessionInfo(**session_data)
    return None


def build_context_block(prev_session: Optional[SessionInfo], context_seed: Optional[str]) -> str:
    """Constrói o bloco de contexto usando lógica nativa Python (sem {{#if}} frágil)."""
    if context_seed and prev_session:
        return (
            f"**Sessão anterior:** {prev_session.session_id}\n\n"
            f"<context_seed>\n{context_seed}\n</context_seed>"
        )
    return "Primeira sessão do projeto."


def render_template(session_id: str, llc_step: float, llc_step_id: str,
                    step_name: str, task_context: str, project: str, wave: int,
                    prev_session: Optional[SessionInfo],
                    context_seed: Optional[str], status: str = "in_progress") -> str:
    if not TEMPLATE_FILE.exists():
        logger.error(f"Template não encontrado: {TEMPLATE_FILE}")
        sys.exit(1)

    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    prev_session_id = prev_session.session_id if prev_session else "null"
    context_block = build_context_block(prev_session, context_seed)

    return (template
            .replace("{{session_id}}", session_id)
            .replace("{{llc_step}}", str(llc_step))
            .replace("{{llc_step_id}}", llc_step_id)
            .replace("{{status}}", status)
            .replace("{{llc_step_name}}", step_name)
            .replace("{{project}}", project)
            .replace("{{wave}}", str(wave))
            .replace("{{task_context}}", task_context)
            .replace("{{prev_session_id}}", prev_session_id)
            .replace("{{context_block}}", context_block)
            .replace("{{duration}}", "0"))


def create_session_file(session_id: str, llc_step: float, llc_step_id: str,
                        step_name: str, task_context: str, project: str, wave: int,
                        prev_session: Optional[SessionInfo],
                        context_seed: Optional[str], status: str = "in_progress") -> Path:
    content = render_template(session_id, llc_step, llc_step_id, step_name,
                              task_context, project, wave,
                              prev_session, context_seed, status)
    session_file = SESSIONS_DIR / f"{session_id}.md"
    if session_file.exists():
        raise RuntimeError(
            f"OVERWRITE RECUSADO: {session_file} já existe. Histórico ACE é "
            f"imutável — reexecute initialize_session.py (computa o próximo ID "
            f"livre) ou rode validate-session-write.py --check-latest."
        )
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(content, encoding='utf-8')
    logger.info(f"✅ Sessão criada: {session_file}")
    return session_file


def update_index(session_id: str, llc_step: float, llc_step_id: str, tags: list):
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            index = {"project": "", "sessions": []}
    else:
        index = {"project": "", "sessions": []}

    index["sessions"].append({
        "session_id": session_id,
        "file": f"{session_id}.md",
        "status": "in_progress",
        "llc_step": llc_step,
        "llc_step_id": llc_step_id,
        "tags": tags,
        "timestamp": datetime.now().isoformat()
    })

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info("✅ index.json atualizado")


WORKTREES_DIR = ACE_DIR / "worktrees"


def create_worktree(session_id: str, prp_id: str | None, wave: int) -> Path | None:
    """Cria um git worktree para isolar o workspace desta sessão."""
    WORKTREES_DIR.mkdir(parents=True, exist_ok=True)

    worktree_path = WORKTREES_DIR / session_id

    branch_name = f"prp-{prp_id}/wave-{wave}" if prp_id else f"session/{session_id}"

    logger.info(f"📂 Criando worktree: {worktree_path} (branch: {branch_name})")

    try:
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            capture_output=True, text=True, check=True
        )
        logger.info(f"✅ Worktree criado em {worktree_path}")
        return worktree_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Falha ao criar worktree: {e.stderr}")
        return None


def cleanup_orphan_worktrees() -> int:
    """Remove worktrees sem sessão correspondente."""
    if not WORKTREES_DIR.exists():
        return 0

    removed = 0
    for wt_path in WORKTREES_DIR.iterdir():
        if wt_path.is_dir():
            session_file = SESSIONS_DIR / f"{wt_path.name}.md"
            if not session_file.exists():
                logger.info(f"🧹 Removendo worktree órfão: {wt_path}")
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt_path)],
                    capture_output=True, text=True
                )
                removed += 1
    return removed


def main():
    parser = argparse.ArgumentParser(description="Inicializa uma nova sessão ACE no LLC")
    parser.add_argument("--step", type=normalize_step, required=True,
                        help=f"Etapa LLC (id/alias/número). Válidos: {sorted(REGISTRY)}")
    parser.add_argument("--step-name", type=str, default=None,
                        help="Nome do step (opcional; inferido do mapa se omitido)")
    parser.add_argument("--task", type=str, required=True, help="Contexto da tarefa")
    parser.add_argument("--project", type=str, default="", help="Nome do projeto")
    parser.add_argument("--wave", type=int, default=1, help="Número da onda")
    parser.add_argument("--prp", type=str, default=None, help="ID do PRP (ex: PRP-001)")
    parser.add_argument("--no-worktree", action="store_true",
                        help="Desativa criacao automatica de git worktree (padrao: ativo p/ sessoes com --prp ou steps auto_worktree: 11, 11.1)")
    parser.add_argument("--tags", type=str, nargs="*", default=[], help="Tags da sessão")
    parser.add_argument("--json", action="store_true", help="Output em JSON (para tool calls)")
    args = parser.parse_args()

    ACE_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)

    session_id = get_next_session_id()
    logger.info(f"🆔 Session ID: {session_id}")

    prev_session = get_previous_session()
    context_seed = None
    if prev_session:
        logger.info(f"📍 Sessão anterior: {prev_session.session_id}")
        prev_file = SESSIONS_DIR / prev_session.file
        context_seed = extract_context_seed(prev_file)
        if context_seed:
            logger.info(f"📦 Context seed carregado ({len(context_seed)} chars)")
        else:
            logger.warning("⚠️  Sessão anterior sem context_seed")
    else:
        logger.info("🆕 Primeira sessão do projeto")

    step_name = args.step_name or args.step.name

    session_file = create_session_file(
        session_id=session_id, llc_step=args.step.number, llc_step_id=args.step.id,
        step_name=step_name, task_context=args.task, project=args.project, wave=args.wave,
        prev_session=prev_session, context_seed=context_seed
    )

    update_index(session_id=session_id, llc_step=args.step.number,
                 llc_step_id=args.step.id, tags=args.tags)

    worktree_path = None
    auto_worktree = (args.prp is not None or args.step.auto_worktree) and not args.no_worktree
    if auto_worktree:
        cleanup_orphan_worktrees()
        worktree_path = create_worktree(session_id, args.prp, args.wave)
        if worktree_path:
            logger.info(f"🔀 Sessao isolada em worktree: {worktree_path}")
        else:
            logger.warning("⚠️  Worktree nao criado — continuando no workspace principal")

    result = {
        "session_id": session_id,
        "file": str(session_file),
        "prev_session": prev_session.session_id if prev_session else None,
        "context_seed": context_seed,
        "llc_step": args.step.number,
        "llc_step_id": args.step.id,
        "llc_step_name": step_name,
        "worktree": str(worktree_path) if worktree_path else None,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("✅ SESSÃO INICIALIZADA")
        print(f"{'='*60}")
        print(f"Session ID: {result['session_id']}")
        print(f"Arquivo: {result['file']}")
        print(f"Etapa LLC: {result['llc_step']} — {result['llc_step_name']}")
        if result['prev_session']:
            print(f"Sessão anterior: {result['prev_session']}")
        if result['context_seed']:
            print(f"\n📦 CONTEXT SEED:")
            print(f"{'-'*60}")
            print(result['context_seed'])
            print(f"{'-'*60}")
        print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
