# EcoNode25 Map Viewer

## Commands

```bash
npm install
npm run dev
```

`npm run dev` serves the repo-level `../outputs` directory automatically at `/outputs`. `npm run serve:outputs` is optional and only needed if you want a separate static outputs server.

The viewer can still run standalone, but the main workflow is through `streamlit run econode25_dashboard/app.py`, which can start, embed, open, and stop this viewer from the Streamlit interface.

## Environment

Copy `.env.example` to `.env` and set `VITE_MAPBOX_TOKEN`. The viewer uses `mapbox://styles/mapbox/light-v11`. If the token is unset, the app keeps geometry visible over a blank light background.

## Travel Time

- Select a scenario.
- Set the origin by map click or from the facility/station dropdown.
- Toggle `Land Use` / `Travel Time`.
- Switch between `Walk` and `Bike` to update parcel travel-time choropleths and the table.
