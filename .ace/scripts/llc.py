#!/usr/bin/env python3
"""llc — CLI orquestrador do pipeline Live and Let Code.

Shim de entrada: o comando real vive no pacote `llc/` (veja `llc.py --help`).
Mantido como script de topo para compatibilidade com chamadas existentes
(`python llc.py ...`, `llc.py ...`).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llc import main

if __name__ == "__main__":
    sys.exit(main())
