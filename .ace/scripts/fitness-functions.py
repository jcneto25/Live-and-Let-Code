#!/usr/bin/env python3
"""fitness-functions — entrypoint CLI.

Compatibilidade: a lógica virou o pacote `fitness-functions/`. Callers legados
(code-health.py) invocam este script como subprocess
(`SCRIPTS_DIR / "fitness-functions.py"`); aqui apenas delegamos ao pacote.
"""

import sys

from fitness_functions import main

if __name__ == "__main__":
    sys.exit(main())
