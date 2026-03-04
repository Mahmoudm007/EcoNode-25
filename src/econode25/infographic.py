from __future__ import annotations

import argparse
from pathlib import Path

import svgwrite
from PIL import Image, ImageDraw
from shapely.geometry import shape

from .config import load_scenario
from .generator import build_city


def generate_infographic(scenario: str, seed: int, template: str = "master_plan") -> Path:
    spec = load_scenario(scenario)
    bundle = build_city(spec, seed)
    output_dir = Path("outputs") / scenario / "infographic"
    output_dir.mkdir(parents=True, exist_ok=True)

    canvas = 1600
    half = canvas / 2
    scale = (canvas * 0.42) / spec.radius_m

    def to_canvas(x: float, y: float) -> tuple[float, float]:
        return half + x * scale, half - y * scale

    svg_path = output_dir / f"{template}.svg"
    drawing = svgwrite.Drawing(str(svg_path), size=(canvas, canvas))
    drawing.add(drawing.rect(insert=(0, 0), size=(canvas, canvas), fill="#f7fbff"))
    drawing.add(drawing.text("EcoNode25", insert=(80, 120), fill="#102a43", font_size=54, font_family="Georgia"))
    drawing.add(
        drawing.text(
            f"{scenario.replace('_', ' ').title()} Scenario",
            insert=(80, 170),
            fill="#486581",
            font_size=28,
            font_family="Georgia",
        )
    )
    for parcel in bundle.parcels:
        geom = shape(parcel["geometry_local"])
        color = bundle.categories["landuse"][parcel["properties"]["landuse"]]["color"]
        drawing.add(
            drawing.polygon(
                points=[to_canvas(x, y) for x, y in geom.exterior.coords],
                fill=f"rgb({color[0]},{color[1]},{color[2]})",
                fill_opacity=0.35,
                stroke="#bcccdc",
                stroke_width=1,
            )
        )
    for road in bundle.roads:
        geom = shape(road["geometry_local"])
        hierarchy = road["properties"]["hierarchy"]
        color = bundle.categories["roads"][hierarchy]["color"]
        width = bundle.categories["roads"][hierarchy]["width"] / 2
        drawing.add(
            drawing.polyline(
                points=[to_canvas(x, y) for x, y in geom.coords],
                fill="none",
                stroke=f"rgb({color[0]},{color[1]},{color[2]})",
                stroke_width=width,
                stroke_linecap="round",
            )
        )
    for station in bundle.transit_stations:
        point = shape(station["geometry_local"])
        drawing.add(drawing.circle(center=to_canvas(point.x, point.y), r=5, fill="#1d3557"))
    drawing.save()

    png_path = output_dir / f"{template}.png"
    image = Image.new("RGB", (canvas, canvas), "#f7fbff")
    draw = ImageDraw.Draw(image, "RGBA")
    for parcel in bundle.parcels:
        geom = shape(parcel["geometry_local"])
        color = bundle.categories["landuse"][parcel["properties"]["landuse"]]["color"]
        draw.polygon([to_canvas(x, y) for x, y in geom.exterior.coords], fill=tuple(color + [90]), outline=(188, 204, 220, 255))
    for road in bundle.roads:
        geom = shape(road["geometry_local"])
        hierarchy = road["properties"]["hierarchy"]
        color = bundle.categories["roads"][hierarchy]["color"]
        width = max(1, bundle.categories["roads"][hierarchy]["width"] // 2)
        draw.line([to_canvas(x, y) for x, y in geom.coords], fill=tuple(color + [255]), width=width)
    image.save(png_path, format="PNG")
    return svg_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate EcoNode25 infographic assets.")
    parser.add_argument("--scenario", default="baseline")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--template", default="master_plan")
    args = parser.parse_args()
    generate_infographic(args.scenario, args.seed, args.template)


if __name__ == "__main__":
    main()
