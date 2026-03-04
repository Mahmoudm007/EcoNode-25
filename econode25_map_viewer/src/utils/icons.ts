function svgData(fill: string, label: string): string {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
      <circle cx="32" cy="32" r="28" fill="${fill}" />
      <text x="32" y="39" text-anchor="middle" font-size="24" font-family="Georgia" fill="#ffffff">${label}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

const cache: Record<string, string> = {};

export function iconUrlFor(key: string): string {
  if (cache[key]) {
    return cache[key];
  }
  const map: Record<string, [string, string]> = {
    grocery: ["#2a9d8f", "M"],
    clinic: ["#e63946", "+"],
    school: ["#457b9d", "S"],
    park: ["#4caf50", "P"],
    maas_hub: ["#264653", "H"],
    energy_plant: ["#ffb703", "E"],
    micromobility_hub: ["#8ecae6", "B"]
  };
  const [fill, label] = map[key] ?? ["#7d8597", "?"];
  cache[key] = svgData(fill, label);
  return cache[key];
}
