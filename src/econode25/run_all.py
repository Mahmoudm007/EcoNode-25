from __future__ import annotations

import argparse

from .config import load_scenario
from .exporters import export_bundle
from .generator import build_city
from .infographic import generate_infographic


def run_all(scenario: str, seed: int) -> dict:
    spec = load_scenario(scenario)
    bundle = build_city(spec, seed)
    export_info = export_bundle(bundle)
    generate_infographic(scenario, seed, template="master_plan")
    return export_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the full EcoNode25 scenario package.")
    parser.add_argument("--scenario", default="baseline")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_all(args.scenario, args.seed)


if __name__ == "__main__":
    main()
