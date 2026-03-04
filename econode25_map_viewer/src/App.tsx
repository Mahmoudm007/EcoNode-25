import { AmbientLight, DirectionalLight, LightingEffect } from "@deck.gl/core";
import DeckGL from "@deck.gl/react";
import { startTransition, useEffect, useState } from "react";
import Map from "react-map-gl/mapbox";

import { appConfig } from "./config/defaults";
import { loadScenarioData, type LoadedScenario, type LocalFeature } from "./data/loader";
import { localXYToLonLat, lonLatToLocalXY, projectGeometry } from "./data/projection";
import { createBuildingsLayer } from "./layers/buildingsLayer";
import { createFacilitiesLayer } from "./layers/facilitiesLayer";
import { createParcelsLayer } from "./layers/parcelsLayer";
import { createRoadLayers } from "./layers/roadsLayer";
import { createTransitLayer } from "./layers/transitLayer";
import { createSnapTree, computeTravelTimes, makeAdjacency, snapFeatureToNode, snapParcelToNode } from "./graph/travelTime";
import { ControlPanel } from "./ui/ControlPanel";
import { Inspector } from "./ui/Inspector";
import { Legend } from "./ui/Legend";
import { Toolbar } from "./ui/Toolbar";
import { TravelTimeTable, type TravelRow } from "./ui/TravelTimeTable";
import { downloadZip } from "./utils/downloadZip";
import { saveCanvasScreenshot } from "./utils/screenshot";

const ambientLight = new AmbientLight({ color: [255, 255, 255], intensity: 2.0 });
const directionalLight = new DirectionalLight({
  color: [255, 255, 255],
  intensity: 1.4,
  direction: [-2, -3, -1]
});
const lightingEffect = new LightingEffect({ ambientLight, directionalLight });

function projectFeature(feature: LocalFeature, centerLat: number, centerLon: number) {
  return {
    id: feature.id,
    properties: feature.properties,
    geometry: projectGeometry(feature.geometry, centerLat, centerLon)
  };
}

function featureLabel(feature: LocalFeature) {
  const name =
    feature.properties.name ??
    feature.properties.facility_id ??
    feature.properties.station_id ??
    feature.properties.parcel_id ??
    feature.id;
  return `${name} (${feature.properties.facility_type ?? feature.properties.station_type ?? "feature"})`;
}

function averageForType(rows: TravelRow[], type: string) {
  const matching = rows.filter((row) => row.type === type);
  if (matching.length === 0) {
    return 0;
  }
  return matching.reduce((sum, row) => sum + row.walkMinutes, 0) / matching.length;
}

export default function App() {
  const [scenario, setScenario] = useState(appConfig.scenarios[0]);
  const [data, setData] = useState<LoadedScenario | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [displayMode, setDisplayMode] = useState<"landuse" | "travel">("landuse");
  const [travelMode, setTravelMode] = useState<"walk" | "bike">("walk");
  const [draftCenterLat, setDraftCenterLat] = useState(53.5461);
  const [draftCenterLon, setDraftCenterLon] = useState(-113.4938);
  const [centerLat, setCenterLat] = useState(53.5461);
  const [centerLon, setCenterLon] = useState(-113.4938);
  const [originId, setOriginId] = useState("");
  const [originNodeId, setOriginNodeId] = useState("center");
  const [clickToSetOrigin, setClickToSetOrigin] = useState(false);
  const [pickedFeature, setPickedFeature] = useState<any | null>(null);
  const [viewState, setViewState] = useState<any>({
    longitude: draftCenterLon,
    latitude: draftCenterLat,
    zoom: 12.8,
    pitch: 52,
    bearing: 26
  });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    loadScenarioData(appConfig.outputsBaseUrl, scenario)
      .then((loaded) => {
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setData(loaded);
          setDraftCenterLat(loaded.spec.center_lat);
          setDraftCenterLon(loaded.spec.center_lon);
          setCenterLat(loaded.spec.center_lat);
          setCenterLon(loaded.spec.center_lon);
          setOriginNodeId("center");
          setOriginId("");
          setViewState((current: any) => ({
            ...current,
            longitude: loaded.spec.center_lon,
            latitude: loaded.spec.center_lat
          }));
          setLoading(false);
        });
      })
      .catch((loadError) => {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load scenario");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [scenario]);

  const adjacency = data ? makeAdjacency(data.graphNodes, data.graphEdges) : null;
  const snapTree = data ? createSnapTree(data.graphNodes) : null;
  const featureById = data
    ? Object.fromEntries([...data.facilities, ...data.transitStations].map((feature) => [feature.id, feature]))
    : {};

  const projectedParcels = data ? data.parcels.map((feature) => projectFeature(feature, centerLat, centerLon)) : [];
  const projectedRoads = data ? data.roads.map((feature) => projectFeature(feature, centerLat, centerLon)) : [];
  const projectedBuildings = data ? data.buildings.map((feature) => projectFeature(feature, centerLat, centerLon)) : [];
  const projectedFacilities = data ? data.facilities.map((feature) => projectFeature(feature, centerLat, centerLon)) : [];
  const projectedTransit = data ? data.transitStations.map((feature) => projectFeature(feature, centerLat, centerLon)) : [];

  const travelTimes =
    data && adjacency
      ? computeTravelTimes(adjacency, originNodeId, data.spec.walk_speed_mps ?? 1.4, data.spec.bike_speed_mps ?? 4.2)
      : { walk: {}, bike: {} };

  const parcelTravelWalk: Record<string, number> = {};
  const parcelTravelBike: Record<string, number> = {};
  if (data && snapTree) {
    for (const parcel of data.parcels) {
      const nodeId = snapParcelToNode(parcel, snapTree);
      if (!nodeId) {
        continue;
      }
      parcelTravelWalk[parcel.id] = travelTimes.walk[nodeId] ?? Number.POSITIVE_INFINITY;
      parcelTravelBike[parcel.id] = travelTimes.bike[nodeId] ?? Number.POSITIVE_INFINITY;
    }
  }

  const tableRows: TravelRow[] = [];
  if (data && snapTree) {
    for (const feature of [...data.facilities, ...data.transitStations]) {
      const nodeId = snapFeatureToNode(feature, snapTree);
      if (!nodeId) {
        continue;
      }
      const walkMinutes = travelTimes.walk[nodeId] ?? Number.POSITIVE_INFINITY;
      const bikeMinutes = travelTimes.bike[nodeId] ?? Number.POSITIVE_INFINITY;
      tableRows.push({
        id: feature.id,
        name: feature.properties.name ?? feature.id,
        type: feature.properties.facility_type ?? feature.properties.station_type ?? "unknown",
        walkMinutes,
        bikeMinutes,
        distanceMeters: Number.isFinite(walkMinutes) ? walkMinutes * (data.spec.walk_speed_mps ?? 1.4) * 60 : 0
      });
    }
    for (const parcel of data.parcels.slice(0, 16)) {
      const nodeId = snapParcelToNode(parcel, snapTree);
      if (!nodeId) {
        continue;
      }
      const walkMinutes = travelTimes.walk[nodeId] ?? Number.POSITIVE_INFINITY;
      const bikeMinutes = travelTimes.bike[nodeId] ?? Number.POSITIVE_INFINITY;
      tableRows.push({
        id: `${parcel.id}_sample`,
        name: `Parcel ${parcel.properties.parcel_id}`,
        type: "parcel_sample",
        walkMinutes,
        bikeMinutes,
        distanceMeters: Number.isFinite(walkMinutes) ? walkMinutes * (data.spec.walk_speed_mps ?? 1.4) * 60 : 0
      });
    }
  }

  const travelSummary = {
    parcelsWithin15Walk:
      projectedParcels.length === 0
        ? 0
        : Object.values(parcelTravelWalk).filter((minutes) => Number.isFinite(minutes) && minutes <= 15).length /
          projectedParcels.length,
    parcelsWithin15Bike:
      projectedParcels.length === 0
        ? 0
        : Object.values(parcelTravelBike).filter((minutes) => Number.isFinite(minutes) && minutes <= 15).length /
          projectedParcels.length,
    groceryAvgWalk: averageForType(tableRows, "grocery"),
    clinicAvgWalk: averageForType(tableRows, "clinic"),
    schoolAvgWalk: averageForType(tableRows, "school")
  };

  const travelMinutesByParcel = travelMode === "walk" ? parcelTravelWalk : parcelTravelBike;

  const layers = data
    ? [
        createParcelsLayer({
          features: projectedParcels,
          categories: data.categories,
          displayMode,
          travelMinutesByParcel
        }),
        ...createRoadLayers(projectedRoads, data.categories),
        createBuildingsLayer(projectedBuildings, data.categories),
        createFacilitiesLayer(projectedFacilities),
        createTransitLayer(projectedTransit, data.categories)
      ]
    : [];

  const originOptions = data
    ? [...data.facilities, ...data.transitStations].map((feature) => ({
        id: feature.id,
        label: featureLabel(feature)
      }))
    : [];

  function applyCenter() {
    setCenterLat(draftCenterLat);
    setCenterLon(draftCenterLon);
    setViewState((current: any) => ({
      ...current,
      latitude: draftCenterLat,
      longitude: draftCenterLon
    }));
  }

  function randomizeCenter() {
    const lat = 20 + Math.random() * 35;
    const lon = -125 + Math.random() * 55;
    setDraftCenterLat(Number(lat.toFixed(4)));
    setDraftCenterLon(Number(lon.toFixed(4)));
    setCenterLat(Number(lat.toFixed(4)));
    setCenterLon(Number(lon.toFixed(4)));
    setViewState((current: any) => ({
      ...current,
      latitude: Number(lat.toFixed(4)),
      longitude: Number(lon.toFixed(4))
    }));
  }

  function handleOriginSelection(nextOriginId: string) {
    setOriginId(nextOriginId);
    const feature = featureById[nextOriginId] as LocalFeature | undefined;
    if (!feature || !snapTree) {
      return;
    }
      const nodeId = snapFeatureToNode(feature, snapTree);
      if (nodeId) {
        setOriginNodeId(nodeId);
        if (feature.geometry.type === "Point") {
          const [x, y] = feature.geometry.coordinates as [number, number];
          const [lon, lat] = localXYToLonLat(centerLat, centerLon, x, y);
          setViewState((current: any) => ({
            ...current,
            longitude: lon,
            latitude: lat
          }));
        }
      }
  }

  function handleMapClick(info: any) {
    if (info.object) {
      setPickedFeature(info.object);
    }
    if (!clickToSetOrigin || !snapTree || !info.coordinate) {
      return;
    }
    const [lon, lat] = info.coordinate as [number, number];
    const [x, y] = lonLatToLocalXY(centerLat, centerLon, lon, lat);
    const nearest = snapTree.nearest(x, y);
    if (nearest) {
      setOriginNodeId(nearest.id);
      setOriginId("");
    }
  }

  function handleDownload() {
    if (!data) {
      return;
    }
    downloadZip(`${scenario}-travel-package.zip`, {
      "city_state.json": { scenario, centerLat, centerLon, originNodeId, travelMode, displayMode },
      "boundary_local.json": data.boundary,
      "parcels_local.json": data.parcels,
      "roads_local.json": data.roads,
      "buildings_local.json": data.buildings,
      "facilities_local.json": data.facilities,
      "transit_stations_local.json": data.transitStations,
      "travel_time_table.json": tableRows,
      "parcel_travel_minutes.json": travelMinutesByParcel,
      "graph_summary.json": { nodes: data.graphNodes.length, edges: data.graphEdges.length }
    });
  }

  function handleSaveView() {
    localStorage.setItem(
      "econode25:view_state",
      JSON.stringify({ scenario, centerLat, centerLon, originNodeId, displayMode, travelMode, viewState })
    );
  }

  return (
    <div className="app-shell">
      <DeckGL
        effects={[lightingEffect]}
        layers={layers}
        viewState={viewState}
        onViewStateChange={({ viewState: nextViewState }) => setViewState(nextViewState)}
        controller={{
          scrollZoom: true,
          dragPan: true,
          dragRotate: true,
          touchZoom: true,
          touchRotate: true
        }}
        onClick={handleMapClick}
        getTooltip={({ object }: any) =>
          object
            ? {
                text:
                  object.properties?.name ??
                  object.properties?.facility_type ??
                  object.properties?.station_type ??
                  object.properties?.parcel_id ??
                  object.properties?.road_id ??
                  "Feature"
              }
            : null
        }
      >
        {appConfig.mapboxToken ? (
          <Map
            mapboxAccessToken={appConfig.mapboxToken}
            mapStyle={appConfig.mapStyle}
            reuseMaps
            attributionControl={false}
          />
        ) : (
          <div className="blank-basemap" />
        )}
      </DeckGL>

      <Toolbar onScreenshot={saveCanvasScreenshot} onDownload={handleDownload} onSaveView={handleSaveView} />

      <ControlPanel
        scenarios={appConfig.scenarios}
        scenario={scenario}
        seed={data?.seed}
        centerLat={draftCenterLat}
        centerLon={draftCenterLon}
        displayMode={displayMode}
        travelMode={travelMode}
        clickToSetOrigin={clickToSetOrigin}
        originId={originId}
        originOptions={originOptions}
        onScenarioChange={setScenario}
        onCenterLatChange={setDraftCenterLat}
        onCenterLonChange={setDraftCenterLon}
        onApplyCenter={applyCenter}
        onRandomizeCenter={randomizeCenter}
        onDisplayModeChange={setDisplayMode}
        onTravelModeChange={setTravelMode}
        onClickToSetOriginChange={setClickToSetOrigin}
        onOriginChange={handleOriginSelection}
      />

      <Legend categories={data?.categories} displayMode={displayMode} />
      <TravelTimeTable rows={tableRows} summary={travelSummary} />
      <Inspector feature={pickedFeature} />

      {loading && <div className="status-banner">Loading scenario data...</div>}
      {error && <div className="status-banner error-banner">{error}</div>}
    </div>
  );
}
