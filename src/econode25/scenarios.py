from __future__ import annotations

from .config import SCENARIO_DIR


def list_scenarios() -> list[str]:
    return sorted(path.stem for path in SCENARIO_DIR.glob("*.yaml"))
