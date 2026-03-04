from econode25.config import load_scenario
from econode25.generator import build_city
from econode25.projection import lonlat_to_local_xy, local_xy_to_lonlat


def test_generator_is_deterministic():
    spec = load_scenario("baseline")
    first = build_city(spec, 42)
    second = build_city(spec, 42)
    assert len(first.parcels) == len(second.parcels)
    assert len(first.roads) == len(second.roads)
    assert len(first.buildings) == len(second.buildings)
    assert first.parcels[0]["geometry_local"] == second.parcels[0]["geometry_local"]
    assert first.graph_edges.equals(second.graph_edges)


def test_projection_round_trip():
    lon, lat = local_xy_to_lonlat(53.5461, -113.4938, 1250, -850)
    x, y = lonlat_to_local_xy(53.5461, -113.4938, lon, lat)
    assert abs(x - 1250) < 1e-6
    assert abs(y + 850) < 1e-6
