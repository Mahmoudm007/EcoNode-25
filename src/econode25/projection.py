from __future__ import annotations

from math import cos, pi
from typing import Iterable


METERS_PER_DEG_LAT = 110_540.0


def local_xy_to_lonlat(center_lat: float, center_lon: float, x_m: float, y_m: float) -> tuple[float, float]:
    lon_scale = 111_320.0 * max(cos(center_lat * pi / 180.0), 1e-6)
    lon = center_lon + x_m / lon_scale
    lat = center_lat + y_m / METERS_PER_DEG_LAT
    return lon, lat


def lonlat_to_local_xy(center_lat: float, center_lon: float, lon: float, lat: float) -> tuple[float, float]:
    lon_scale = 111_320.0 * max(cos(center_lat * pi / 180.0), 1e-6)
    x_m = (lon - center_lon) * lon_scale
    y_m = (lat - center_lat) * METERS_PER_DEG_LAT
    return x_m, y_m


def transform_coords(
    center_lat: float,
    center_lon: float,
    coords: Iterable[tuple[float, float]],
) -> list[tuple[float, float]]:
    return [local_xy_to_lonlat(center_lat, center_lon, x, y) for x, y in coords]
