#!/usr/bin/env python3
"""Permite `python3 -m fitness-functions` além do shim fitness-functions.py."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
