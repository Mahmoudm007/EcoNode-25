import { useDeferredValue, useState } from "react";

export interface TravelRow {
  id: string;
  name: string;
  type: string;
  walkMinutes: number;
  bikeMinutes: number;
  distanceMeters: number;
}

interface TravelTimeTableProps {
  rows: TravelRow[];
  summary: {
    parcelsWithin15Walk: number;
    parcelsWithin15Bike: number;
    groceryAvgWalk: number;
    clinicAvgWalk: number;
    schoolAvgWalk: number;
  };
}

export function TravelTimeTable({ rows, summary }: TravelTimeTableProps) {
  const [filter, setFilter] = useState("all");
  const [sortBy, setSortBy] = useState<"walk" | "bike">("walk");
  const deferredFilter = useDeferredValue(filter);

  const visibleRows = [...rows.filter((row) => deferredFilter === "all" || row.type === deferredFilter)].sort(
    (left, right) => (sortBy === "walk" ? left.walkMinutes - right.walkMinutes : left.bikeMinutes - right.bikeMinutes)
  );

  const types = Array.from(new Set(rows.map((row) => row.type))).sort();

  return (
    <aside className="panel table-panel">
      <div className="table-header">
        <h2>Travel Times</h2>
        <div className="button-row">
          <button onClick={() => setSortBy("walk")} className={sortBy === "walk" ? "active" : ""}>
            Sort Walk
          </button>
          <button onClick={() => setSortBy("bike")} className={sortBy === "bike" ? "active" : ""}>
            Sort Bike
          </button>
        </div>
      </div>
      <label>
        <span>Destination Filter</span>
        <select value={filter} onChange={(event) => setFilter(event.currentTarget.value)}>
          <option value="all">All</option>
          {types.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>
      <div className="summary-grid">
        <div>% parcels within 15 min walk: {(summary.parcelsWithin15Walk * 100).toFixed(0)}%</div>
        <div>% parcels within 15 min bike: {(summary.parcelsWithin15Bike * 100).toFixed(0)}%</div>
        <div>Avg grocery walk: {summary.groceryAvgWalk.toFixed(1)} min</div>
        <div>Avg clinic walk: {summary.clinicAvgWalk.toFixed(1)} min</div>
        <div>Avg school walk: {summary.schoolAvgWalk.toFixed(1)} min</div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Walk</th>
              <th>Bike</th>
              <th>Dist (m)</th>
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row) => (
              <tr key={row.id}>
                <td>{row.name}</td>
                <td>{row.type}</td>
                <td>{row.walkMinutes.toFixed(1)}</td>
                <td>{row.bikeMinutes.toFixed(1)}</td>
                <td>{row.distanceMeters.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </aside>
  );
}
