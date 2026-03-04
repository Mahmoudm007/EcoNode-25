from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from shapely.geometry import shape

# Ensure Streamlit resolves the local package before any globally installed
# package with the same name.
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
MAP_VIEWER_DIR = ROOT_DIR / "econode25_map_viewer"
MAP_VIEWER_HOST = "127.0.0.1"
MAP_VIEWER_PORT = 5173
MAP_VIEWER_URL = f"http://{MAP_VIEWER_HOST}:{MAP_VIEWER_PORT}"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from econode25.config import load_scenario
from econode25.exporters import export_bundle, export_scenario_package
from econode25.generator import build_city
from econode25.scenarios import list_scenarios


def _npm_executable() -> str | None:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _viewer_is_reachable() -> bool:
    try:
        with urlopen(MAP_VIEWER_URL, timeout=0.75) as response:
            return response.status < 500
    except (OSError, URLError):
        return False


def _start_map_viewer() -> tuple[bool, str]:
    if _viewer_is_reachable():
        return True, "Map viewer is already running."

    existing_process = st.session_state.get("map_viewer_process")
    if existing_process is not None and existing_process.poll() is None:
        deadline = time.time() + 12.0
        while time.time() < deadline:
            if _viewer_is_reachable():
                return True, "Map viewer started."
            time.sleep(0.4)
        return False, "Map viewer is still starting. Wait a few seconds and use Refresh."

    npm_exec = _npm_executable()
    if not npm_exec:
        return False, "npm was not found on PATH. Install Node.js and run `npm install` in `econode25_map_viewer`."

    if not MAP_VIEWER_DIR.exists():
        return False, f"Map viewer folder not found: {MAP_VIEWER_DIR}"

    command = [npm_exec, "run", "dev", "--", "--host", MAP_VIEWER_HOST, "--port", str(MAP_VIEWER_PORT)]
    creationflags = 0
    startupinfo = None
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        process = subprocess.Popen(
            command,
            cwd=MAP_VIEWER_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
    except OSError as exc:
        return False, f"Failed to start the map viewer: {exc}"

    st.session_state["map_viewer_process"] = process
    st.session_state["map_viewer_pid"] = process.pid

    deadline = time.time() + 12.0
    while time.time() < deadline:
        if _viewer_is_reachable():
            return True, "Map viewer started."
        if process.poll() is not None:
            st.session_state.pop("map_viewer_process", None)
            st.session_state.pop("map_viewer_pid", None)
            return False, "Map viewer exited before becoming ready. Run `npm install` in `econode25_map_viewer` and try again."
        time.sleep(0.4)

    return False, "Map viewer is still starting. Wait a few seconds and use Refresh."


def _stop_map_viewer() -> tuple[bool, str]:
    process = st.session_state.get("map_viewer_process")
    if process is None:
        st.session_state.pop("map_viewer_pid", None)
        return False, "No managed map viewer process is attached to this Streamlit session."

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    st.session_state.pop("map_viewer_process", None)
    st.session_state.pop("map_viewer_pid", None)
    return True, "Map viewer stopped."


def _build_preview(bundle) -> go.Figure:
    fig = go.Figure()
    for parcel in bundle.parcels:
        geom = shape(parcel["geometry_local"])
        xs, ys = geom.exterior.xy
        fig.add_trace(
            go.Scatter(
                x=list(xs),
                y=list(ys),
                mode="lines",
                line={"width": 1, "color": "rgba(120,140,160,0.6)"},
                fill="toself",
                fillcolor="rgba(118,174,103,0.14)",
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for road in bundle.roads:
        geom = shape(road["geometry_local"])
        xs, ys = geom.xy
        width = {"ring_arterial": 3, "radial_arterial": 2}.get(road["properties"]["hierarchy"], 1)
        fig.add_trace(
            go.Scatter(
                x=list(xs),
                y=list(ys),
                mode="lines",
                line={"width": width, "color": "rgba(29,53,87,0.85)"},
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for station in bundle.transit_stations:
        pt = shape(station["geometry_local"])
        fig.add_trace(
            go.Scatter(
                x=[pt.x],
                y=[pt.y],
                mode="markers",
                marker={"size": 6, "color": "#e63946"},
                name="Transit",
                hovertext=station["properties"]["name"],
                showlegend=False,
            )
        )
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        xaxis={"visible": False},
        yaxis={"visible": False, "scaleanchor": "x", "scaleratio": 1},
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=520,
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="EcoNode25 Dashboard", layout="wide")
    st.title("EcoNode25 Scenario Dashboard")

    if "map_viewer_autostart" not in st.session_state:
        st.session_state["map_viewer_autostart"] = True
    if "map_viewer_status" not in st.session_state:
        st.session_state["map_viewer_status"] = ""
    if st.session_state["map_viewer_autostart"] and not _viewer_is_reachable():
        started, message = _start_map_viewer()
        st.session_state["map_viewer_status"] = message
        if not started:
            st.session_state["map_viewer_autostart"] = False

    scenario_name = st.sidebar.selectbox("Scenario", list_scenarios(), index=0)
    seed = st.sidebar.number_input("Seed", min_value=0, value=42, step=1)

    base_spec = load_scenario(scenario_name)
    density_factor = st.sidebar.slider("Density", 0.7, 1.4, float(base_spec.density_factor), 0.05)
    renewables_pct = st.sidebar.slider("Renewables %", 0.1, 0.9, float(base_spec.renewables_pct), 0.05)
    transit_investment = st.sidebar.slider("Transit Investment", 0.2, 1.0, float(base_spec.transit_investment), 0.05)
    green_ratio = st.sidebar.slider("Green Ratio", 0.1, 0.4, float(base_spec.green_ratio), 0.02)

    spec = load_scenario(scenario_name)
    spec = spec.__class__(
        **{
            **spec.to_dict(),
            "density_factor": density_factor,
            "renewables_pct": renewables_pct,
            "transit_investment": transit_investment,
            "green_ratio": green_ratio,
        }
    )

    bundle = build_city(spec, int(seed))
    export_info = export_bundle(bundle)
    analytics = export_info["analytics"]

    dashboard_tab, map_tab = st.tabs(["Dashboard", "3D Map Viewer"])

    with dashboard_tab:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Population", analytics["accessibility_summary"]["population_total"])
        kpi2.metric("Walk 15-Min Share", f'{analytics["accessibility_summary"]["walk_15min_parcel_share"]:.1%}')
        kpi3.metric("Bike 15-Min Share", f'{analytics["accessibility_summary"]["bike_15min_parcel_share"]:.1%}')
        kpi4.metric("SDG 11", analytics["sdg_scores"]["sdg_11_cities"])

        left, right = st.columns([1.35, 1.0])
        with left:
            st.subheader("Map Preview")
            st.plotly_chart(_build_preview(bundle), use_container_width=True)
        with right:
            st.subheader("Travel Time Summary")
            st.dataframe(
                analytics["travel_time_stats"].sort_values("walk_time_min").head(12),
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Mean Walk Time by Type")
            st.json(analytics["mean_walk_times_by_type"])

        st.subheader("Accessibility Table")
        st.dataframe(analytics["accessibility_table"], use_container_width=True, hide_index=True)

        if st.button("Export Scenario Package"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = Path(export_info["scenario_dir"])
            target = Path("exports") / f"{timestamp}_{scenario_name}"
            export_scenario_package(source, target)
            st.success(f"Exported to {target}")

    with map_tab:
        st.subheader("Integrated 3D Map Viewer")
        st.caption("The React + deck.gl map viewer runs as a managed local process and is embedded below.")

        control_col1, control_col2, control_col3, control_col4 = st.columns([1.1, 1.1, 1.2, 2.4])
        with control_col1:
            if st.button("Start / Restart Viewer", use_container_width=True):
                st.session_state["map_viewer_autostart"] = True
                started, message = _start_map_viewer()
                st.session_state["map_viewer_status"] = message
                if not started:
                    st.session_state["map_viewer_autostart"] = False
        with control_col2:
            if st.button("Stop Viewer", use_container_width=True):
                st.session_state["map_viewer_autostart"] = False
                _, message = _stop_map_viewer()
                st.session_state["map_viewer_status"] = message
        with control_col3:
            if st.button("Refresh Status", use_container_width=True):
                st.session_state["map_viewer_status"] = (
                    "Map viewer is reachable." if _viewer_is_reachable() else "Map viewer is not reachable."
                )
        with control_col4:
            st.link_button("Open Map Viewer Full Screen", MAP_VIEWER_URL, use_container_width=True)

        if st.session_state["map_viewer_status"]:
            st.info(st.session_state["map_viewer_status"])

        if _viewer_is_reachable():
            components.iframe(MAP_VIEWER_URL, height=840, scrolling=False)
        else:
            st.warning(
                "The map viewer is not reachable yet. If this is the first run, install the frontend once with "
                "`cd econode25_map_viewer && npm install`, then use Start / Restart Viewer."
            )
            st.code("cd econode25_map_viewer\nnpm install\nnpm run dev", language="bash")


if __name__ == "__main__":
    main()
