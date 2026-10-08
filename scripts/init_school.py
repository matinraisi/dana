"""Deprecated alias — use ``scripts/init_academy_org.py``.

Previously hardcoded a Suntech organization name. That behavior is removed.
Pass the real customer organization title explicitly.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

print(
    "NOTE: scripts/init_school.py is deprecated. "
    'Use: python scripts/init_academy_org.py --title "Customer Organization Name"',
    file=sys.stderr,
)

target = Path(__file__).resolve().with_name("init_academy_org.py")
sys.argv = [str(target), *sys.argv[1:]]
runpy.run_path(str(target), run_name="__main__")
