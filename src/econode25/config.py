from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT_DIR / "configs" / "scenarios"


@dataclass(frozen=True)
class CitySpec:
    name: str
    radius_m: float
    rings: int
    spokes: int
    density_factor: float
    transit_investment: float
    green_ratio: float
    renewables_pct: float
    walk_speed_mps: float
    bike_speed_mps: float
    population_target: int
    center_lat: float
    center_lon: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_scenario(name: str) -> CitySpec:
    path = SCENARIO_DIR / f"{name}.yaml"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in SCENARIO_DIR.glob("*.yaml")))
        raise FileNotFoundError(f"Unknown scenario '{name}'. Available: {available}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return CitySpec(**data)
