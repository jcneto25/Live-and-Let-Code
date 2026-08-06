#!/usr/bin/env python3
"""finalize_session — extração de tags do arquivo de sessão."""

import re

from .paths import logger


def _strip_comments(content: str) -> str:
    """Remove conteúdo que NÃO é tag real da sessão atual.

    1. Comentários HTML (placeholders <!-- <tag> --> do template) — evita
       tags fantasmas de aprendizados/bloqueadores/gate/tarefas/feedback
       ainda não preenchidas.
    2. Blocos <context_seed>...</context_seed> — metadados de estado
       (sessão anterior no Contexto, placeholders no Encerramento). Podem
       conter texto com tags literais (ex.: descrição de action que citava
       `<action_log>`/`<action>`), que poluiriam a extração com fantasma
       [type=?] — bug observado na sessão 2026-08-06-018.
    """
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    content = re.sub(r'<context_seed>.*?</context_seed>', '', content,
                     flags=re.DOTALL)
    return content


def extract_all_tags(content: str, tag: str) -> list[dict]:
    content = _strip_comments(content)
    # \b evita casar tags-filhas/container (ex.: <action_log> não é <action>),
    # o que engolia o primeiro <action> real num fantasma [type=?] (bug latente
    # descoberto na sessão 2026-08-06-017 — o seed perdia o 1º action).
    pattern = f'<{tag}\\b([^>]*)>(.*?)</{tag}>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({"attrs": attrs, "content": body.strip()})
    return results


def extract_actions(content: str) -> list[dict]:
    return extract_all_tags(content, "action")


def extract_learning_points(content: str) -> list[dict]:
    return extract_all_tags(content, "learning_point")


def extract_blockers(content: str) -> list[dict]:
    return extract_all_tags(content, "blocker")


def extract_files_touched(content: str) -> list[str]:
    """Paths unicos dos <file_delta> no corpo da sessao (ordem de aparicao).

    Base para popular `tags` no index.json — habilita queries do tipo
    "quais sessoes tocaram o arquivo X" sem ler cada .md (o campo deixava
    de ser vestigial).
    """
    clean = _strip_comments(content)
    paths = re.findall(r'<file_delta>(.*?)</file_delta>', clean, re.DOTALL)
    seen: list[str] = []
    for p in paths:
        p = p.strip()
        if p and p not in seen:
            seen.append(p)
    return seen


def extract_task_completions(content: str) -> list[dict]:
    """Extrai tarefas concluídas das tags <task_completed>."""
    content = _strip_comments(content)
    pattern = r'<task_completed([^>]*)>(.*?)</task_completed>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({
            "task_id": attrs.get("id", ""),
            "prp": attrs.get("prp", ""),
            "status": attrs.get("status", "done"),
            "description": body.strip()
        })
    return results


def extract_skill_feedback(content: str) -> list[dict]:
    """Extrai sugestões de melhoria de skills via <skill_feedback>."""
    content = _strip_comments(content)
    pattern = r'<skill_feedback([^>]*)>(.*?)</skill_feedback>'
    matches = re.findall(pattern, content, re.DOTALL)
    results = []
    for attrs_str, body in matches:
        attrs = {}
        for attr_match in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
            attrs[attr_match.group(1)] = attr_match.group(2)
        results.append({
            "skill": attrs.get("skill", "unknown"),
            "priority": attrs.get("priority", "medium"),
            "content": body.strip()
        })
    return results
