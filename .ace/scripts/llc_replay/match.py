from typing import Optional

from .cache import load_cache

# ── Match Algorithm (A) ──

def extract_entities(text: str) -> list:
    return [w.lower() for w in text.replace('"', '').replace("'", '').split()
            if len(w) > 2 and w.isalpha()]


def find_best_script(task_type: str, task_description: str) -> Optional[dict]:
    scripts = load_cache(task_type)
    if not scripts:
        return None

    entities = extract_entities(task_description)
    best = None
    best_score = 0.0

    for script in scripts:
        params = set(script.get("params_used", []))
        if not params:
            keyword_score = 0.5
        else:
            keyword_score = len(params & set(entities)) / len(params)

        final_score = keyword_score

        if final_score > best_score:
            best_score = final_score
            best = script

    threshold = 0.60
    if best_score >= threshold:
        return best
    return None
