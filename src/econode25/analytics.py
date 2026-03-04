from __future__ import annotations

from collections import defaultdict
from math import inf
from typing import Any

import networkx as nx
import pandas as pd
from shapely.geometry import Point, shape

from .generator import CityBundle


def _nearest_node_id(point: Point, nodes_df: pd.DataFrame) -> str:
    distances = (nodes_df["x_m"] - point.x) ** 2 + (nodes_df["y_m"] - point.y) ** 2
    idx = distances.idxmin()
    return str(nodes_df.loc[idx, "node_id"])


def _filtered_graph(graph: nx.Graph, mode: str) -> nx.Graph:
    allow_key = "bike_allowed" if mode == "bike" else "walk_allowed"
    filtered = nx.Graph()
    filtered.add_nodes_from(graph.nodes(data=True))
    for u, v, data in graph.edges(data=True):
        if data.get(allow_key, False):
            filtered.add_edge(u, v, **data)
    return filtered


def _parcel_centroids(bundle: CityBundle) -> pd.DataFrame:
    rows = []
    for parcel in bundle.parcels:
        geom = shape(parcel["geometry_local"])
        rows.append(
            {
                "parcel_id": parcel["id"],
                "landuse": parcel["properties"]["landuse"],
                "population": parcel["properties"]["population"],
                "centroid": geom.centroid,
            }
        )
    return pd.DataFrame(rows)


def _destinations(bundle: CityBundle) -> pd.DataFrame:
    rows = []
    for feature in bundle.facilities:
        rows.append(
            {
                "dest_id": feature["id"],
                "name": feature["properties"]["name"],
                "dest_type": feature["properties"]["facility_type"],
                "geometry": shape(feature["geometry_local"]),
            }
        )
    for feature in bundle.transit_stations:
        rows.append(
            {
                "dest_id": feature["id"],
                "name": feature["properties"]["name"],
                "dest_type": feature["properties"]["station_type"],
                "geometry": shape(feature["geometry_local"]),
            }
        )
    return pd.DataFrame(rows)


def compute_analytics(bundle: CityBundle) -> dict[str, Any]:
    parcels_df = _parcel_centroids(bundle)
    destinations_df = _destinations(bundle)
    nodes_df = bundle.graph_nodes.copy()

    walk_graph = _filtered_graph(bundle.graph, "walk")
    bike_graph = _filtered_graph(bundle.graph, "bike")

    dest_groups = defaultdict(list)
    for _, row in destinations_df.iterrows():
        dest_groups[row["dest_type"]].append(row)

    parcel_rows = []
    mean_walk_times: dict[str, list[float]] = defaultdict(list)
    walk_covered = 0
    bike_covered = 0

    for _, parcel in parcels_df.iterrows():
        origin_node = _nearest_node_id(parcel["centroid"], nodes_df)
        walk_lengths = nx.single_source_dijkstra_path_length(
            walk_graph,
            origin_node,
            weight=lambda _u, _v, data: data["length_m"] / bundle.spec.walk_speed_mps / 60.0,
        )
        bike_lengths = nx.single_source_dijkstra_path_length(
            bike_graph,
            origin_node,
            weight=lambda _u, _v, data: data["length_m"] / bundle.spec.bike_speed_mps / 60.0,
        )
        nearest_by_type = {}
        for dest_type, rows in dest_groups.items():
            best_walk = inf
            best_bike = inf
            for row in rows:
                dest_node = _nearest_node_id(row["geometry"], nodes_df)
                best_walk = min(best_walk, walk_lengths.get(dest_node, inf))
                best_bike = min(best_bike, bike_lengths.get(dest_node, inf))
            nearest_by_type[dest_type] = {"walk": best_walk, "bike": best_bike}
            if best_walk < inf:
                mean_walk_times[dest_type].append(best_walk)

        essential = ("grocery", "clinic", "school", "central_station", "ring_station")
        essential_walk = [nearest_by_type[key]["walk"] for key in essential if key in nearest_by_type]
        essential_bike = [nearest_by_type[key]["bike"] for key in essential if key in nearest_by_type]
        within_walk = all(value <= 15 for value in essential_walk if value < inf)
        within_bike = all(value <= 15 for value in essential_bike if value < inf)
        walk_covered += int(within_walk)
        bike_covered += int(within_bike)

        parcel_rows.append(
            {
                "parcel_id": parcel["parcel_id"],
                "landuse": parcel["landuse"],
                "population": parcel["population"],
                "within_15_walk": within_walk,
                "within_15_bike": within_bike,
                "nearest_grocery_walk_min": round(nearest_by_type.get("grocery", {}).get("walk", inf), 2),
                "nearest_clinic_walk_min": round(nearest_by_type.get("clinic", {}).get("walk", inf), 2),
                "nearest_school_walk_min": round(nearest_by_type.get("school", {}).get("walk", inf), 2),
            }
        )

    center_walk = nx.single_source_dijkstra_path_length(
        walk_graph,
        "center",
        weight=lambda _u, _v, data: data["length_m"] / bundle.spec.walk_speed_mps / 60.0,
    )
    center_bike = nx.single_source_dijkstra_path_length(
        bike_graph,
        "center",
        weight=lambda _u, _v, data: data["length_m"] / bundle.spec.bike_speed_mps / 60.0,
    )
    travel_rows = []
    for _, row in destinations_df.iterrows():
        dest_node = _nearest_node_id(row["geometry"], nodes_df)
        travel_rows.append(
            {
                "destination_id": row["dest_id"],
                "name": row["name"],
                "destination_type": row["dest_type"],
                "walk_time_min": round(center_walk.get(dest_node, inf), 2),
                "bike_time_min": round(center_bike.get(dest_node, inf), 2),
            }
        )

    accessibility_summary = {
        "scenario": bundle.spec.name,
        "seed": bundle.seed,
        "population_total": int(parcels_df["population"].sum()),
        "parcel_count": len(bundle.parcels),
        "walk_15min_parcel_share": round(walk_covered / max(len(bundle.parcels), 1), 3),
        "bike_15min_parcel_share": round(bike_covered / max(len(bundle.parcels), 1), 3),
    }
    sustainability_summary = {
        "scenario": bundle.spec.name,
        "green_ratio": bundle.spec.green_ratio,
        "transit_investment": bundle.spec.transit_investment,
        "renewables_pct": bundle.spec.renewables_pct,
        "walk_coverage_score": round(accessibility_summary["walk_15min_parcel_share"] * 100, 1),
        "bike_coverage_score": round(accessibility_summary["bike_15min_parcel_share"] * 100, 1),
        "green_space_score": round(min(bundle.spec.green_ratio / 0.3, 1.0) * 100, 1),
        "energy_score": round(bundle.spec.renewables_pct * 100, 1),
    }
    sdg_scores = {
        "sdg_3_health": round((sustainability_summary["walk_coverage_score"] + sustainability_summary["green_space_score"]) / 2.0, 1),
        "sdg_7_energy": sustainability_summary["energy_score"],
        "sdg_11_cities": round(
            (
                sustainability_summary["walk_coverage_score"]
                + sustainability_summary["bike_coverage_score"]
                + bundle.spec.transit_investment * 100
            )
            / 3.0,
            1,
        ),
        "sdg_13_climate": round((sustainability_summary["energy_score"] + sustainability_summary["green_space_score"]) / 2.0, 1),
    }
    mean_walk_times_by_type = {
        dest_type: round(sum(values) / len(values), 2)
        for dest_type, values in mean_walk_times.items()
        if values
    }

    return {
        "accessibility_summary": accessibility_summary,
        "accessibility_table": pd.DataFrame(parcel_rows),
        "travel_time_stats": pd.DataFrame(travel_rows),
        "sustainability_summary": sustainability_summary,
        "sdg_scores": sdg_scores,
        "mean_walk_times_by_type": mean_walk_times_by_type,
    }
