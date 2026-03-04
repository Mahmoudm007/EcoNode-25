interface InspectorProps {
  feature: any | null;
}

export function Inspector({ feature }: InspectorProps) {
  return (
    <aside className="panel inspector-panel">
      <h2>Inspector</h2>
      {feature ? <pre>{JSON.stringify(feature.properties ?? feature.object?.properties ?? {}, null, 2)}</pre> : <p>Click a parcel, road, building, facility, or station.</p>}
    </aside>
  );
}
