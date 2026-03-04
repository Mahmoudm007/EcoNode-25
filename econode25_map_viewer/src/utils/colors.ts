export function withAlpha(color: number[], alpha: number): [number, number, number, number] {
  return [color[0] ?? 200, color[1] ?? 200, color[2] ?? 200, alpha];
}

export function roadInnerColor(color: number[]): [number, number, number, number] {
  return [
    Math.min((color[0] ?? 180) + 36, 255),
    Math.min((color[1] ?? 180) + 36, 255),
    Math.min((color[2] ?? 180) + 36, 255),
    255
  ];
}
