from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (REPO_ROOT / "demo/00_repo_baseline/fixture").resolve()

fixture_root_str = str(FIXTURE_ROOT)
if fixture_root_str not in sys.path:
    # Ensure tests can import demo fixture modules as `src.*` after relocating
    # fixture code under demo/00_repo_baseline/fixture.
    sys.path.insert(0, fixture_root_str)
