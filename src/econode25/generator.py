from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from shapely import LineString, Point, Polygon, affinity
from shapely.geometry import mapping

from .categories import default_categories
from .config import CitySpec
from .projection import local_xy_to_lonlat


RING_LANDUSE = [
    "green_heart",
    "mixed_use",
    "high_density_residential",
    "medium_density_residential",
    "urban_agriculture",
    "mobility_buffer",
]

FACILITY_TYPES = [
    "grocery",
    "clinic",
    "school",
    "park",
    "maas_hub",
    "energy_plant",
    "micromobility_hub",
]


@dataclass
class CityBundle:
    spec: CitySpec
    seed: int
    categories: dict[str, Any]
    boundary: dict[str, Any]
    parcels: list[dict[str, Any]]
    roads: list[dict[str, Any]]
    buildings: list[dict[str, Any]]
    facilities: list[dict[str, Any]]
    transit_stations: list[dict[str, Any]]
    graph: nx.Graph
    graph_nodes: pd.DataFrame
    graph_edges: pd.DataFrame


def _circle_sector(inner_r: float, outer_r: float, start_a: float, end_a: float, steps: int = 24) -> Polygon:
    outer = [
        (outer_r * cos(theta), outer_r * sin(theta))
        for theta in np.linspace(start_a, end_a, steps, endpoint=True)
    ]
    inner = [
        (inner_r * cos(theta), inner_r * sin(theta))
        for theta in np.linspace(end_a, start_a, steps, endpoint=True)
    ]
    return Polygon(outer + inner)


def _feature_record(feature_id: str, geometry, properties: dict[str, Any], spec: CitySpec) -> dict[str, Any]:
    if geometry.geom_type == "Polygon":
        coords = [
            [local_xy_to_lonlat(spec.center_lat, spec.center_lon, x, y) for x, y in geometry.exterior.coords]
        ]
        geometry_wgs84 = {"type": "Polygon", "coordinates": coords}
    elif geometry.geom_type == "LineString":
        coords = [local_xy_to_lonlat(spec.center_lat, spec.center_lon, x, y) for x, y in geometry.coords]
        geometry_wgs84 = {"type": "LineString", "coordinates": coords}
    else:
        lon, lat = local_xy_to_lonlat(spec.center_lat, spec.center_lon, geometry.x, geometry.y)
        geometry_wgs84 = {"type": "Point", "coordinates": [lon, lat]}
    return {
        "id": feature_id,
        "geometry_local": mapping(geometry),
        "geometry_wgs84": geometry_wgs84,
        "properties": properties,
    }


def _geometry_payload(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": feature["id"],
            "geometry": feature["geometry_local"],
            "properties": feature["properties"],
        }
        for feature in features
    ]


def _node_id(ring_index: int, spoke_index: int) -> str:
    return f"n_{ring_index}_{spoke_index}"


def build_city(spec: CitySpec, seed: int) -> CityBundle:
    rng = np.random.default_rng(seed)
    categories = default_categories()
    ring_count = min(max(spec.rings, 5), 6)
    ring_edges = np.linspace(0.0, spec.radius_m, ring_count + 1)
    angles = np.linspace(0.0, 2.0 * pi, spec.spokes, endpoint=False)

    boundary_geom = Point(0.0, 0.0).buffer(spec.radius_m, quad_segs=96)
    boundary = _feature_record(
        "boundary",
        boundary_geom,
        {"scenario": spec.name, "radius_m": spec.radius_m},
        spec,
    )

    parcels: list[dict[str, Any]] = []
    roads: list[dict[str, Any]] = []
    buildings: list[dict[str, Any]] = []
    facilities: list[dict[str, Any]] = []
    transit_stations: list[dict[str, Any]] = []

    parcel_population_weights: list[float] = []
    for ring_index in range(ring_count):
        inner_r = ring_edges[ring_index]
        outer_r = ring_edges[ring_index + 1]
        landuse = RING_LANDUSE[min(ring_index, len(RING_LANDUSE) - 1)]
        density_scale = spec.density_factor * (1.75 - 0.24 * ring_index)
        for sector_index, start_a in enumerate(angles):
            end_a = angles[(sector_index + 1) % len(angles)] if sector_index + 1 < len(angles) else 2.0 * pi
            parcel_geom = _circle_sector(inner_r, outer_r, start_a, end_a)
            parcel_id = f"parcel_{ring_index}_{sector_index}"
            area = parcel_geom.area
            parcel_population_weights.append(max(area * max(density_scale, 0.2), 1.0))
            parcels.append(
                _feature_record(
                    parcel_id,
                    parcel_geom,
                    {
                        "parcel_id": parcel_id,
                        "ring_index": ring_index,
                        "sector_index": sector_index,
                        "landuse": landuse,
                        "area_m2": round(area, 2),
                    },
                    spec,
                )
            )

            centroid = parcel_geom.centroid
            connector = LineString(
                [
                    (
                        inner_r * cos((start_a + end_a) / 2.0),
                        inner_r * sin((start_a + end_a) / 2.0),
                    ),
                    (centroid.x, centroid.y),
                    (
                        outer_r * cos((start_a + end_a) / 2.0),
                        outer_r * sin((start_a + end_a) / 2.0),
                    ),
                ]
            )
            roads.append(
                _feature_record(
                    f"road_local_{ring_index}_{sector_index}",
                    connector,
                    {
                        "road_id": f"road_local_{ring_index}_{sector_index}",
                        "hierarchy": "local_connector",
                        "ring_index": ring_index,
                    },
                    spec,
                )
            )

            building_count = 1 if ring_index == 0 else 2 + int(ring_index < 3)
            for building_index in range(building_count):
                width = (outer_r - inner_r) * (0.22 + 0.05 * rng.random())
                depth = width * (0.55 + 0.2 * rng.random())
                footprint = Polygon(
                    [
                        (-width / 2, -depth / 2),
                        (width / 2, -depth / 2),
                        (width / 2, depth / 2),
                        (-width / 2, depth / 2),
                    ]
                )
                angle = float(start_a + (end_a - start_a) * (0.25 + 0.5 * (building_index + 1) / (building_count + 1)))
                radius = inner_r + (outer_r - inner_r) * (0.4 + 0.15 * building_index)
                rotated = affinity.rotate(footprint, angle * 180.0 / pi, origin=(0.0, 0.0))
                moved = affinity.translate(rotated, xoff=radius * cos(angle), yoff=radius * sin(angle))
                padded = parcel_geom.buffer(-6.0)
                if not padded.is_empty and not padded.contains(moved):
                    moved = moved.intersection(padded)
                if moved.is_empty:
                    continue
                height_m = max(8.0, (ring_count - ring_index + 1) * 4.5 * spec.density_factor + rng.uniform(2, 8))
                building_id = f"bldg_{ring_index}_{sector_index}_{building_index}"
                buildings.append(
                    _feature_record(
                        building_id,
                        moved,
                        {
                            "building_id": building_id,
                            "parcel_id": parcel_id,
                            "landuse": landuse,
                            "height_m": round(float(height_m), 2),
                            "floors": int(round(height_m / 3.2)),
                        },
                        spec,
                    )
                )

            if ring_index in (1, 2, 3) and sector_index % max(1, spec.spokes // 4) == 0:
                facility_type = FACILITY_TYPES[(ring_index + sector_index) % len(FACILITY_TYPES)]
                facility_id = f"facility_{ring_index}_{sector_index}"
                facilities.append(
                    _feature_record(
                        facility_id,
                        centroid,
                        {
                            "facility_id": facility_id,
                            "name": f"{facility_type.replace('_', ' ').title()} {ring_index}-{sector_index}",
                            "facility_type": facility_type,
                            "parcel_id": parcel_id,
                        },
                        spec,
                    )
                )

    total_weight = float(sum(parcel_population_weights))
    population = [
        int(round(spec.population_target * weight / max(total_weight, 1.0)))
        for weight in parcel_population_weights
    ]
    delta = spec.population_target - sum(population)
    if population:
        population[0] += delta
    for parcel, pop in zip(parcels, population, strict=False):
        parcel["properties"]["population"] = pop
        parcel["properties"]["households"] = max(1, int(round(pop / 2.4)))

    graph = nx.Graph()
    graph.add_node("center", x_m=0.0, y_m=0.0)
    center_lon, center_lat = local_xy_to_lonlat(spec.center_lat, spec.center_lon, 0.0, 0.0)
    node_rows: list[dict[str, Any]] = [
        {
            "node_id": "center",
            "x_m": 0.0,
            "y_m": 0.0,
            "lon": center_lon,
            "lat": center_lat,
        }
    ]
    edge_rows: list[dict[str, Any]] = []

    ring_radii = ring_edges[1:]
    for spoke_index, angle in enumerate(angles):
        spoke_coords = [(0.0, 0.0)]
        previous = "center"
        previous_radius = 0.0
        for ring_index, radius in enumerate(ring_radii, start=1):
            x = float(radius * cos(angle))
            y = float(radius * sin(angle))
            node_id = _node_id(ring_index, spoke_index)
            graph.add_node(node_id, x_m=x, y_m=y)
            lon, lat = local_xy_to_lonlat(spec.center_lat, spec.center_lon, x, y)
            node_rows.append({"node_id": node_id, "x_m": x, "y_m": y, "lon": lon, "lat": lat})
            spoke_coords.append((x, y))
            edge_length = float(radius - previous_radius)
            bike_allowed = not (ring_index == 1 and spoke_index % 3 == 0)
            graph.add_edge(
                previous,
                node_id,
                length_m=edge_length,
                hierarchy="radial_arterial",
                bike_allowed=bike_allowed,
                walk_allowed=True,
            )
            edge_rows.append(
                {
                    "edge_id": f"edge_{previous}_{node_id}",
                    "u": previous,
                    "v": node_id,
                    "length_m": round(edge_length, 2),
                    "hierarchy": "radial_arterial",
                    "bike_allowed": bike_allowed,
                    "walk_allowed": True,
                }
            )
            previous = node_id
            previous_radius = radius
        roads.append(
            _feature_record(
                f"road_spoke_{spoke_index}",
                LineString(spoke_coords),
                {
                    "road_id": f"road_spoke_{spoke_index}",
                    "hierarchy": "radial_arterial",
                    "spoke_index": spoke_index,
                },
                spec,
            )
        )

    for ring_index, radius in enumerate(ring_radii, start=1):
        ring_coords = []
        for spoke_index, angle in enumerate(angles):
            x = float(radius * cos(angle))
            y = float(radius * sin(angle))
            ring_coords.append((x, y))
            next_spoke = (spoke_index + 1) % len(angles)
            next_node = _node_id(ring_index, next_spoke)
            node_id = _node_id(ring_index, spoke_index)
            segment_length = float(2.0 * radius * sin(pi / len(angles)))
            hierarchy = "ring_arterial" if ring_index <= 2 else "local_connector"
            graph.add_edge(
                node_id,
                next_node,
                length_m=segment_length,
                hierarchy=hierarchy,
                bike_allowed=True,
                walk_allowed=True,
            )
            edge_rows.append(
                {
                    "edge_id": f"edge_{node_id}_{next_node}",
                    "u": node_id,
                    "v": next_node,
                    "length_m": round(segment_length, 2),
                    "hierarchy": hierarchy,
                    "bike_allowed": True,
                    "walk_allowed": True,
                }
            )
        roads.append(
            _feature_record(
                f"road_ring_{ring_index}",
                LineString(ring_coords + [ring_coords[0]]),
                {
                    "road_id": f"road_ring_{ring_index}",
                    "hierarchy": "ring_arterial",
                    "ring_index": ring_index,
                },
                spec,
            )
        )

    transit_stations.append(
        _feature_record(
            "station_central",
            Point(0.0, 0.0),
            {
                "station_id": "station_central",
                "name": "Central Station",
                "station_type": "central_station",
            },
            spec,
        )
    )
    station_ring_radius = ring_radii[1] if len(ring_radii) > 1 else ring_radii[0]
    ring_station_count = max(8, min(12, spec.spokes + 2))
    for station_index, angle in enumerate(np.linspace(0.0, 2.0 * pi, ring_station_count, endpoint=False)):
        x = float(station_ring_radius * cos(angle))
        y = float(station_ring_radius * sin(angle))
        transit_stations.append(
            _feature_record(
                f"station_ring_{station_index}",
                Point(x, y),
                {
                    "station_id": f"station_ring_{station_index}",
                    "name": f"Ring Station {station_index + 1}",
                    "station_type": "ring_station",
                },
                spec,
            )
        )
    for spoke_index, angle in enumerate(angles):
        for stop_index, radius in enumerate(np.linspace(spec.radius_m * 0.35, spec.radius_m * 0.85, 3)):
            x = float(radius * cos(angle))
            y = float(radius * sin(angle))
            transit_stations.append(
                _feature_record(
                    f"stop_{spoke_index}_{stop_index}",
                    Point(x, y),
                    {
                        "station_id": f"stop_{spoke_index}_{stop_index}",
                        "name": f"Spoke {spoke_index + 1} Stop {stop_index + 1}",
                        "station_type": "spoke_stop",
                    },
                    spec,
                )
            )

    return CityBundle(
        spec=spec,
        seed=seed,
        categories=categories,
        boundary=boundary,
        parcels=parcels,
        roads=roads,
        buildings=buildings,
        facilities=facilities,
        transit_stations=transit_stations,
        graph=graph,
        graph_nodes=pd.DataFrame(node_rows),
        graph_edges=pd.DataFrame(edge_rows),
    )


def local_xy_payload(bundle: CityBundle) -> dict[str, Any]:
    return {
        "boundary": {
            "id": bundle.boundary["id"],
            "geometry": bundle.boundary["geometry_local"],
            "properties": bundle.boundary["properties"],
        },
        "parcels": _geometry_payload(bundle.parcels),
        "roads": _geometry_payload(bundle.roads),
        "buildings": _geometry_payload(bundle.buildings),
        "facilities": _geometry_payload(bundle.facilities),
        "transit_stations": _geometry_payload(bundle.transit_stations),
    }
