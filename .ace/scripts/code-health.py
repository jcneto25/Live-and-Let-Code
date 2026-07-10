#!/usr/bin/env python3
"""code-health — entrypoint CLI.

Compatibilidade: a lógica virou o pacote `code_health/`. Callers invocam este
script como subprocess. Aqui apenas delegamos ao pacote.
"""

import sys

from code_health import main

if __name__ == "__main__":
    sys.exit(main())
