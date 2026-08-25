"""Compatibility wrapper for the source-checkout project generator."""

from __future__ import annotations

import sys

from esimu_core.scaffold import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
