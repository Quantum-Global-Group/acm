"""Shared pytest fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the project root importable so `import backend...` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure tests always run in simulate mode regardless of operator env.
os.environ.setdefault("SETTLEMENT_SIMULATE", "true")
