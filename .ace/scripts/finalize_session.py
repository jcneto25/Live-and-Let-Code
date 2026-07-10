#!/usr/bin/env python3
"""finalize_session — entrypoint CLI.

Compatibilidade: a lógica virou o pacote `finalize_session/`. Callers
(harness/session.py, subprocess) invocam este script; aqui apenas delegamos.
"""

import sys

from finalize_session import main

if __name__ == "__main__":
    sys.exit(main())
