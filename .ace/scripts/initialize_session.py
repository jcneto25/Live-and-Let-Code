#!/usr/bin/env python3
"""initialize_session — entrypoint CLI.

Compatibilidade: a lógica virou o pacote `initialize_session/`. Callers
(harness/session.py, subprocess) invocam este script; aqui apenas delegamos.
"""

import sys

from initialize_session import main

if __name__ == "__main__":
    sys.exit(main())
