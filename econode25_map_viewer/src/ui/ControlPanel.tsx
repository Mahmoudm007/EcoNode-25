import type { ChangeEvent } from "react";

interface OriginOption {
  id: string;
  label: string;
}

interface ControlPanelProps {
  scenarios: string[];
  scenario: string;
  seed?: number;
  centerLat: number;
  centerLon: number;
  displayMode: "landuse" | "travel";
  travelMode: "walk" | "bike";
  clickToSetOrigin: boolean;
  originId: string;
  originOptions: OriginOption[];
  onScenarioChange: (value: string) => void;
  onCenterLatChange: (value: number) => void;
  onCenterLonChange: (value: number) => void;
  onApplyCenter: () => void;
  onRandomizeCenter: () => void;
  onDisplayModeChange: (value: "landuse" | "travel") => void;
  onTravelModeChange: (value: "walk" | "bike") => void;
  onClickToSetOriginChange: (value: boolean) => void;
  onOriginChange: (value: string) => void;
}

function numberValue(event: ChangeEvent<HTMLInputElement>) {
  return Number(event.currentTarget.value);
}

export function ControlPanel(props: ControlPanelProps) {
  return (
    <aside className="panel control-panel">
      <h2>Controls</h2>
      <label>
        <span>Scenario</span>
        <select value={props.scenario} onChange={(event) => props.onScenarioChange(event.currentTarget.value)}>
          {props.scenarios.map((scenario) => (
            <option key={scenario} value={scenario}>
              {scenario}
            </option>
          ))}
        </select>
      </label>
      <div className="seed-row">Seed: {props.seed ?? "..."}</div>
      <label>
        <span>Center Latitude</span>
        <input type="number" value={props.centerLat} step="0.0001" onChange={(event) => props.onCenterLatChange(numberValue(event))} />
      </label>
      <label>
        <span>Center Longitude</span>
        <input type="number" value={props.centerLon} step="0.0001" onChange={(event) => props.onCenterLonChange(numberValue(event))} />
      </label>
      <div className="button-row">
        <button onClick={props.onApplyCenter}>Apply</button>
        <button onClick={props.onRandomizeCenter}>Randomize</button>
      </div>
      <label>
        <span>Map Mode</span>
        <select
          value={props.displayMode}
          onChange={(event) => props.onDisplayModeChange(event.currentTarget.value as "landuse" | "travel")}
        >
          <option value="landuse">Land Use</option>
          <option value="travel">Travel Time</option>
        </select>
      </label>
      <label>
        <span>Travel Mode</span>
        <select
          value={props.travelMode}
          onChange={(event) => props.onTravelModeChange(event.currentTarget.value as "walk" | "bike")}
        >
          <option value="walk">Walk</option>
          <option value="bike">Bike</option>
        </select>
      </label>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={props.clickToSetOrigin}
          onChange={(event) => props.onClickToSetOriginChange(event.currentTarget.checked)}
        />
        <span>Click on map to set origin</span>
      </label>
      <label>
        <span>Origin from list</span>
        <select value={props.originId} onChange={(event) => props.onOriginChange(event.currentTarget.value)}>
          <option value="">Select...</option>
          {props.originOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </aside>
  );
}
