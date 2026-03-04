interface LegendProps {
  categories: any;
  displayMode: "landuse" | "travel";
}

function swatch(color: number[]) {
  return { backgroundColor: `rgb(${color[0]}, ${color[1]}, ${color[2]})` };
}

export function Legend({ categories, displayMode }: LegendProps) {
  if (!categories) {
    return null;
  }
  return (
    <aside className="panel legend-panel">
      <h2>Legend</h2>
      <div className="legend-section">
        <h3>Land Use</h3>
        {Object.entries(categories.landuse ?? {}).map(([key, entry]: [string, any]) => (
          <div key={key} className="legend-row">
            <span className="legend-swatch" style={swatch(entry.color)} />
            <span>{key.replaceAll("_", " ")}</span>
          </div>
        ))}
      </div>
      <div className="legend-section">
        <h3>Roads</h3>
        {Object.entries(categories.roads ?? {}).map(([key, entry]: [string, any]) => (
          <div key={key} className="legend-row">
            <span className="legend-line" style={{ backgroundColor: `rgb(${entry.color.join(",")})`, height: Math.max(2, entry.width / 3) }} />
            <span>{key.replaceAll("_", " ")}</span>
          </div>
        ))}
      </div>
      <div className="legend-section">
        <h3>Facilities</h3>
        {Object.entries(categories.facilities ?? {}).map(([key, entry]: [string, any]) => (
          <div key={key} className="legend-row">
            <span className="legend-swatch" style={swatch(entry.color)} />
            <span>{key.replaceAll("_", " ")}</span>
          </div>
        ))}
      </div>
      <div className="legend-section">
        <h3>Transit</h3>
        {Object.entries(categories.transit ?? {}).map(([key, entry]: [string, any]) => (
          <div key={key} className="legend-row">
            <span className="legend-swatch" style={swatch(entry.color)} />
            <span>{key.replaceAll("_", " ")}</span>
          </div>
        ))}
      </div>
      {displayMode === "travel" && (
        <div className="legend-section">
          <h3>Travel Time (min)</h3>
          {(categories.travel_time_bins ?? []).map((entry: any) => (
            <div key={entry.label} className="legend-row">
              <span className="legend-swatch" style={swatch(entry.color)} />
              <span>{entry.label}</span>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
