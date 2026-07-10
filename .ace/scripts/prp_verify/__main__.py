#!/usr/bin/env python3
"""Permite `python3 -m prp_verify` além do shim prp_verify.py."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
