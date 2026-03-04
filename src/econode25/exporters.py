from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import shape

from .analytics import compute_analytics
from .generator import CityBundle, local_xy_payload


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _feature_collection(features: list[dict[str, Any]], geometry_key: str) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": feature["id"],
                "geometry": feature[geometry_key],
                "properties": feature["properties"],
            }
            for feature in features
        ],
    }


def _write_geojson(path: Path, features: list[dict[str, Any]]) -> None:
    _write_json(path, _feature_collection(features, "geometry_wgs84"))


def _write_summary(path_base: Path, payload: dict[str, Any]) -> None:
    _write_json(path_base.with_suffix(".json"), payload)
    pd.DataFrame([payload]).to_csv(path_base.with_suffix(".csv"), index=False)


def _graph_summary(bundle: CityBundle) -> dict[str, Any]:
    return {
        "node_count": int(len(bundle.graph_nodes)),
        "edge_count": int(len(bundle.graph_edges)),
        "walk_speed_mps": bundle.spec.walk_speed_mps,
        "bike_speed_mps": bundle.spec.bike_speed_mps,
    }


def _make_master_plan_png(output_dir: Path, bundle: CityBundle) -> None:
    figures_dir = output_dir / "figures"
    _ensure_dir(figures_dir)
    fig, ax = plt.subplots(figsize=(8, 8))
    for parcel in bundle.parcels:
        geom = shape(parcel["geometry_local"])
        xs, ys = geom.exterior.xy
        ax.fill(xs, ys, alpha=0.25)
    for road in bundle.roads:
        geom = shape(road["geometry_local"])
        xs, ys = geom.xy
        lw = {"ring_arterial": 2.0, "radial_arterial": 1.5}.get(road["properties"]["hierarchy"], 0.75)
        ax.plot(xs, ys, linewidth=lw, color="#3a506b")
    for station in bundle.transit_stations:
        pt = shape(station["geometry_local"])
        ax.scatter([pt.x], [pt.y], s=18, color="#1d3557")
    ax.set_title(f"{bundle.spec.name.replace('_', ' ').title()} Master Plan")
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.savefig(figures_dir / "master_plan.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def _make_travel_time_png(output_dir: Path, travel_df: pd.DataFrame) -> None:
    figures_dir = output_dir / "figures"
    _ensure_dir(figures_dir)
    if travel_df.empty:
        return
    top = travel_df.nsmallest(12, "walk_time_min")
    fig, ax = plt.subplots(figsize=(10, 5))
    positions = range(len(top))
    ax.bar(positions, top["walk_time_min"], width=0.4, label="Walk")
    ax.bar([p + 0.4 for p in positions], top["bike_time_min"], width=0.4, label="Bike")
    ax.set_xticks([p + 0.2 for p in positions])
    ax.set_xticklabels(top["name"], rotation=45, ha="right")
    ax.set_ylabel("Minutes")
    ax.set_title("Travel Time from Central Station")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "travel_times.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def _write_report(output_dir: Path, bundle: CityBundle, analytics: dict[str, Any]) -> None:
    report_dir = output_dir / "reports"
    _ensure_dir(report_dir)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>EcoNode25 Report - {bundle.spec.name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #102a43; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }}
    .card {{ border: 1px solid #d9e2ec; border-radius: 12px; padding: 1rem; background: #f7fbff; }}
    pre {{ white-space: pre-wrap; word-break: break-word; }}
  </style>
</head>
<body>
  <h1>EcoNode25 Scenario Report</h1>
  <p>Scenario: <strong>{bundle.spec.name}</strong> | Seed: <strong>{bundle.seed}</strong></p>
  <div class="grid">
    <div class="card"><h2>Accessibility</h2><pre>{json.dumps(analytics["accessibility_summary"], indent=2)}</pre></div>
    <div class="card"><h2>Sustainability</h2><pre>{json.dumps(analytics["sustainability_summary"], indent=2)}</pre></div>
    <div class="card"><h2>SDG Proxies</h2><pre>{json.dumps(analytics["sdg_scores"], indent=2)}</pre></div>
  </div>
</body>
</html>
"""
    with (report_dir / "report.html").open("w", encoding="utf-8") as handle:
        handle.write(html)


def export_bundle(bundle: CityBundle, root: Path | None = None) -> dict[str, Any]:
    root_dir = Path(root) if root is not None else Path("outputs")
    scenario_dir = root_dir / bundle.spec.name
    data_wgs84_dir = scenario_dir / "data_wgs84"
    data_local_dir = scenario_dir / "data_localxy"
    network_dir = scenario_dir / "network"
    metadata_dir = scenario_dir / "metadata"
    metrics_dir = scenario_dir / "metrics"
    for path in [data_wgs84_dir, data_local_dir, network_dir, metadata_dir, metrics_dir]:
        _ensure_dir(path)

    _write_geojson(data_wgs84_dir / "boundary.geojson", [bundle.boundary])
    _write_geojson(data_wgs84_dir / "parcels.geojson", bundle.parcels)
    _write_geojson(data_wgs84_dir / "roads.geojson", bundle.roads)
    _write_geojson(data_wgs84_dir / "buildings.geojson", bundle.buildings)
    _write_geojson(data_wgs84_dir / "facilities.geojson", bundle.facilities)
    _write_geojson(data_wgs84_dir / "transit_stations.geojson", bundle.transit_stations)

    local_payload = local_xy_payload(bundle)
    _write_json(data_local_dir / "boundary_local.json", local_payload["boundary"])
    _write_json(data_local_dir / "parcels_local.json", local_payload["parcels"])
    _write_json(data_local_dir / "roads_local.json", local_payload["roads"])
    _write_json(data_local_dir / "buildings_local.json", local_payload["buildings"])
    _write_json(data_local_dir / "facilities_local.json", local_payload["facilities"])
    _write_json(data_local_dir / "transit_stations_local.json", local_payload["transit_stations"])

    adjacency: dict[str, list[dict[str, Any]]] = {}
    for edge in bundle.graph_edges.to_dict(orient="records"):
        adjacency.setdefault(edge["u"], []).append(
            {
                "to": edge["v"],
                "length_m": edge["length_m"],
                "hierarchy": edge["hierarchy"],
                "bike_allowed": edge["bike_allowed"],
                "walk_allowed": edge["walk_allowed"],
            }
        )
        adjacency.setdefault(edge["v"], []).append(
            {
                "to": edge["u"],
                "length_m": edge["length_m"],
                "hierarchy": edge["hierarchy"],
                "bike_allowed": edge["bike_allowed"],
                "walk_allowed": edge["walk_allowed"],
            }
        )
    _write_json(data_local_dir / "network_graph.json", adjacency)

    bundle.graph_nodes.to_csv(network_dir / "graph_nodes.csv", index=False)
    bundle.graph_edges.to_csv(network_dir / "graph_edges.csv", index=False)
    _write_json(network_dir / "adjacency.json", adjacency)
    _write_json(network_dir / "graph_summary.json", _graph_summary(bundle))

    _write_json(metadata_dir / "categories.json", bundle.categories)
    _write_json(
        metadata_dir / "city_state.json",
        {
            "scenario": bundle.spec.name,
            "seed": bundle.seed,
            "spec": bundle.spec.to_dict(),
        },
    )

    analytics = compute_analytics(bundle)
    _write_summary(metrics_dir / "accessibility_summary", analytics["accessibility_summary"])
    analytics["accessibility_table"].to_csv(metrics_dir / "accessibility_table.csv", index=False)
    analytics["travel_time_stats"].to_csv(metrics_dir / "travel_time_stats.csv", index=False)
    _write_summary(metrics_dir / "sustainability_summary", analytics["sustainability_summary"])
    _write_json(metrics_dir / "sdg_scores.json", analytics["sdg_scores"])

    underserved = []
    access_rows = analytics["accessibility_table"].to_dict(orient="records")
    by_id = {parcel["id"]: parcel for parcel in bundle.parcels}
    for row in access_rows:
        if not row["within_15_walk"]:
            parcel = by_id[row["parcel_id"]]
            underserved.append(
                {
                    "type": "Feature",
                    "id": parcel["id"],
                    "geometry": parcel["geometry_wgs84"],
                    "properties": row,
                }
            )
    _write_json(metrics_dir / "underserved_zones.geojson", {"type": "FeatureCollection", "features": underserved})

    _make_master_plan_png(scenario_dir, bundle)
    _make_travel_time_png(scenario_dir, analytics["travel_time_stats"])
    _write_report(scenario_dir, bundle, analytics)
    return {"scenario_dir": str(scenario_dir), "analytics": analytics}


def export_scenario_package(source: Path, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    return target
