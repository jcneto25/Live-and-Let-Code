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
    python .ace/scripts/initialize_session.py --step 0.5 --task "Visão Estratégica"
    python .ace/scripts/initialize_session.py --step 5 --task "Refatoração JWT" --project tjce-audit --wave 1
    python .ace/scripts/initialize_session.py --step 0.1 --task "Conversão Docling" --json
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"
TEMPLATE_FILE = ACE_DIR / "templates" / "session.template.md"

LLC_STEPS = {
    0: "Ingestão",
    0.1: "Conversão (Docling)",
    0.5: "Visão + Módulos",
    1: "7 Especificações",
    2: "PRDs",
    3: "PRPs",
    4: "Planejamento",
    5: "Arquitetura",
    6: "Tarefas",
    7: "Design System",
    8: "Setup + Mock Data",
    9: "Documentação de Testes",
    10: "Documentos do Projeto",
    11: "Execução",
}

VALID_STEPS = frozenset(LLC_STEPS.keys())


@dataclass
class SessionInfo:
    session_id: str
    file: str
    status: str
    llc_step: float
    tags: list
    timestamp: str


def extract_context_seed(session_file: Path) -> Optional[str]:
    if not session_file.exists():
        return None
    content = session_file.read_text(encoding='utf-8')
    match = re.search(r'<context_seed>(.*?)</context_seed>', content, re.DOTALL)
    return match.group(1).strip() if match else None


def get_next_session_id() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if not SESSIONS_DIR.exists():
        return f"{today}-001"
    todays_sessions = list(SESSIONS_DIR.glob(f"{today}-*.md"))
    return f"{today}-{len(todays_sessions) + 1:03d}"


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


def render_template(session_id: str, llc_step: float, step_name: str,
                    task_context: str, project: str, wave: int,
                    prev_session: Optional[SessionInfo],
                    context_seed: Optional[str]) -> str:
    if not TEMPLATE_FILE.exists():
        logger.error(f"Template não encontrado: {TEMPLATE_FILE}")
        sys.exit(1)

    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    prev_session_id = prev_session.session_id if prev_session else "null"
    context_block = build_context_block(prev_session, context_seed)

    return (template
            .replace("{{session_id}}", session_id)
            .replace("{{llc_step}}", str(llc_step))
            .replace("{{llc_step_name}}", step_name)
            .replace("{{project}}", project)
            .replace("{{wave}}", str(wave))
            .replace("{{task_context}}", task_context)
            .replace("{{prev_session_id}}", prev_session_id)
            .replace("{{context_block}}", context_block)
            .replace("{{duration}}", "0"))


def create_session_file(session_id: str, llc_step: float, step_name: str,
                        task_context: str, project: str, wave: int,
                        prev_session: Optional[SessionInfo],
                        context_seed: Optional[str]) -> Path:
    content = render_template(session_id, llc_step, step_name,
                              task_context, project, wave,
                              prev_session, context_seed)
    session_file = SESSIONS_DIR / f"{session_id}.md"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(content, encoding='utf-8')
    logger.info(f"✅ Sessão criada: {session_file}")
    return session_file


def update_index(session_id: str, llc_step: float, tags: list):
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
        "tags": tags,
        "timestamp": datetime.now().isoformat()
    })

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info("✅ index.json atualizado")


def main():
    parser = argparse.ArgumentParser(description="Inicializa uma nova sessão ACE no LLC")
    parser.add_argument("--step", type=float, required=True,
                        help=f"Etapa LLC. Valores válidos: {sorted(VALID_STEPS)}")
    parser.add_argument("--step-name", type=str, default=None,
                        help="Nome do step (opcional; inferido do mapa se omitido)")
    parser.add_argument("--task", type=str, required=True, help="Contexto da tarefa")
    parser.add_argument("--project", type=str, default="", help="Nome do projeto")
    parser.add_argument("--wave", type=int, default=1, help="Número da onda")
    parser.add_argument("--tags", type=str, nargs="*", default=[], help="Tags da sessão")
    parser.add_argument("--json", action="store_true", help="Output em JSON (para tool calls)")
    args = parser.parse_args()

    if args.step not in VALID_STEPS:
        logger.error(f"Step inválido: {args.step}. Valores válidos: {sorted(VALID_STEPS)}")
        sys.exit(1)

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

    step_name = args.step_name or LLC_STEPS.get(args.step, f"Etapa {args.step}")

    session_file = create_session_file(
        session_id=session_id, llc_step=args.step, step_name=step_name,
        task_context=args.task, project=args.project, wave=args.wave,
        prev_session=prev_session, context_seed=context_seed
    )

    update_index(session_id=session_id, llc_step=args.step, tags=args.tags)

    result = {
        "session_id": session_id,
        "file": str(session_file),
        "prev_session": prev_session.session_id if prev_session else None,
        "context_seed": context_seed,
        "llc_step": args.step,
        "llc_step_name": step_name
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
