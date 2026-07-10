#!/usr/bin/env python3
"""prp_verify — entrypoint CLI.

Compatibilidade: a lógica virou o pacote `prp_verify/`. Callers legados
(harness, llc_wave) invocam este script como subprocess
(`SCRIPTS_DIR / "prp_verify.py"`); aqui apenas delegamos ao pacote.
"""

import sys

from prp_verify import main

if __name__ == "__main__":
    sys.exit(main())
