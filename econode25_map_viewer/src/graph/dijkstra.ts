import type { AdjacencyMap } from "./adjacency";

interface QueueNode {
  id: string;
  priority: number;
}

class MinHeap {
  private readonly items: QueueNode[] = [];

  push(item: QueueNode) {
    this.items.push(item);
    this.bubbleUp(this.items.length - 1);
  }

  pop(): QueueNode | undefined {
    if (this.items.length === 0) {
      return undefined;
    }
    const top = this.items[0];
    const last = this.items.pop()!;
    if (this.items.length > 0) {
      this.items[0] = last;
      this.bubbleDown(0);
    }
    return top;
  }

  get size(): number {
    return this.items.length;
  }

  private bubbleUp(index: number) {
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.items[parent].priority <= this.items[index].priority) {
        break;
      }
      [this.items[parent], this.items[index]] = [this.items[index], this.items[parent]];
      index = parent;
    }
  }

  private bubbleDown(index: number) {
    while (true) {
      const left = index * 2 + 1;
      const right = left + 1;
      let smallest = index;
      if (left < this.items.length && this.items[left].priority < this.items[smallest].priority) {
        smallest = left;
      }
      if (right < this.items.length && this.items[right].priority < this.items[smallest].priority) {
        smallest = right;
      }
      if (smallest === index) {
        break;
      }
      [this.items[smallest], this.items[index]] = [this.items[index], this.items[smallest]];
      index = smallest;
    }
  }
}

export function dijkstra(
  adjacency: AdjacencyMap,
  origin: string,
  getWeight: (from: string, to: string, edge: AdjacencyMap[string][number]) => number | undefined
): Record<string, number> {
  const distances: Record<string, number> = { [origin]: 0 };
  const heap = new MinHeap();
  heap.push({ id: origin, priority: 0 });

  while (heap.size > 0) {
    const current = heap.pop()!;
    if (current.priority > (distances[current.id] ?? Number.POSITIVE_INFINITY)) {
      continue;
    }
    for (const edge of adjacency[current.id] ?? []) {
      const weight = getWeight(current.id, edge.to, edge);
      if (weight === undefined) {
        continue;
      }
      const candidate = current.priority + weight;
      if (candidate < (distances[edge.to] ?? Number.POSITIVE_INFINITY)) {
        distances[edge.to] = candidate;
        heap.push({ id: edge.to, priority: candidate });
      }
    }
  }
  return distances;
}
