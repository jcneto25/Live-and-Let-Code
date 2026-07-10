import json
import sys

import llc_steps


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            try:
                s = llc_steps.normalize_step(arg)
                print(
                    f"{arg!r:>22} -> id={s.id:<5} num={s.number:<5} "
                    f"skill={s.skill_file} gate={s.gate}"
                )
            except llc_steps.UnknownStepError as e:
                print(f"{arg!r:>22} -> ERRO: {e}")
    else:
        print(
            json.dumps(
                {
                    s.id: {
                        "number": s.number,
                        "name": s.name,
                        "skill_file": s.skill_file,
                        "gate": s.gate,
                        "in_pipeline": s.in_pipeline,
                        "auto_worktree": s.auto_worktree,
                        "aliases": list(s.aliases),
                    }
                    for s in sorted(
                        llc_steps.REGISTRY.values(), key=lambda x: x.number
                    )
                },
                indent=2,
                ensure_ascii=False,
            )
        )
