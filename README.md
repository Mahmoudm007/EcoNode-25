# econode25_platform_v3

`econode25_platform_v3` is a standalone research prototype that procedurally generates a circular 15-minute city, exports analytics-ready datasets, provides a Streamlit dashboard, renders a cover-ready infographic, and feeds a professional React + deck.gl web map viewer.

## Structure

- `configs/scenarios/*.yaml`: scenario parameters
- `src/econode25/`: generator, analytics, exporters, CLI, infographic
- `econode25_dashboard/`: Streamlit app
- `econode25_map_viewer/`: Vite + React + deck.gl viewer
- `outputs/`: generated scenario outputs
- `exports/`: dashboard scenario package exports
- `tests/`: pytest coverage for core deterministic logic

## Generate City Outputs

```bash
python -m econode25.run_all --scenario baseline --seed 42
```

This creates:

- `outputs/{scenario}/data_wgs84/*.geojson`
- `outputs/{scenario}/data_localxy/*.json`
- `outputs/{scenario}/network/graph_nodes.csv`
- `outputs/{scenario}/network/graph_edges.csv`
- `outputs/{scenario}/metadata/categories.json`
- `outputs/{scenario}/metadata/city_state.json`
- analytics, figures, report assets, and infographic outputs

## Run Dashboard

```bash
streamlit run econode25_dashboard/app.py
```

The dashboard is the primary entrypoint. It exposes scenario controls, KPIs, charts, a local map preview, and an export action that copies the active scenario package into `exports/{timestamp}_{scenario}`.

It also includes a `3D Map Viewer` tab that:

- starts the React + deck.gl viewer for you on `http://127.0.0.1:5173` when possible,
- embeds that viewer directly inside Streamlit,
- provides a full-screen button to open the viewer in its own browser tab,
- provides a stop button so you can close the managed viewer process from Streamlit.

If the embedded viewer does not start on the first run, install frontend dependencies once:

```bash
cd econode25_map_viewer
npm install
```

## Run Web Viewer

```bash
cd econode25_map_viewer
npm install
npm run dev
```

The Vite viewer now serves the repo-level `outputs/` directory automatically at `/outputs` during `npm run dev` and `npm run preview`, so a separate static server is not required for normal local use. `npm run serve:outputs` remains available only if you want a standalone outputs server.

## Mapbox Token

Create `econode25_map_viewer/.env` from `.env.example` and set:

```bash
VITE_MAPBOX_TOKEN=your_mapbox_token
```

The viewer uses the light basemap style `mapbox://styles/mapbox/light-v11`. If no token is set, the app falls back to a blank background while still rendering geometry layers.

## Travel-Time Workflow

1. Generate outputs with `python -m econode25.run_all --scenario baseline --seed 42`.
2. Start the viewer and choose a scenario.
3. Set an origin by enabling map click mode or selecting a facility/transit station from the origin dropdown.
4. Toggle between `Land Use` and `Travel Time`.
5. Switch `Walk` / `Bike` to view parcel choropleths and a sortable travel-time table.
6. Use the center latitude/longitude controls to relocate the city without regenerating topology.
