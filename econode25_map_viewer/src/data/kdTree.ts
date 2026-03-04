export interface KdPoint {
  id: string;
  x: number;
  y: number;
}

interface KdNode {
  point: KdPoint;
  axis: 0 | 1;
  left?: KdNode;
  right?: KdNode;
}

function build(points: KdPoint[], depth = 0): KdNode | undefined {
  if (points.length === 0) {
    return undefined;
  }
  const axis: 0 | 1 = (depth % 2) as 0 | 1;
  const sorted = [...points].sort((a, b) => (axis === 0 ? a.x - b.x : a.y - b.y));
  const index = Math.floor(sorted.length / 2);
  return {
    point: sorted[index],
    axis,
    left: build(sorted.slice(0, index), depth + 1),
    right: build(sorted.slice(index + 1), depth + 1)
  };
}

export class KdTree {
  private readonly root: KdNode | undefined;

  constructor(points: KdPoint[]) {
    this.root = build(points);
  }

  nearest(x: number, y: number): KdPoint | undefined {
    let best: { point: KdPoint; dist: number } | undefined;

    const search = (node?: KdNode) => {
      if (!node) {
        return;
      }
      const dx = x - node.point.x;
      const dy = y - node.point.y;
      const dist = dx * dx + dy * dy;
      if (!best || dist < best.dist) {
        best = { point: node.point, dist };
      }
      const axisDelta = node.axis === 0 ? dx : dy;
      const nearBranch = axisDelta <= 0 ? node.left : node.right;
      const farBranch = axisDelta <= 0 ? node.right : node.left;
      search(nearBranch);
      if (!best || axisDelta * axisDelta < best.dist) {
        search(farBranch);
      }
    };

    search(this.root);
    return best?.point;
  }
}
