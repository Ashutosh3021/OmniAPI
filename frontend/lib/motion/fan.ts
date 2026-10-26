// The concept driver.
//
// One request becomes a fan of parallel calls and gathers back into one answer.
// Every visual that carries the idea is drawn from this module: the branches, the
// packets that travel them, the envelope they land in, and the spine they leave from.
//
// The geometry is resolution-independent (SVG viewBox units). Two orientations are
// generated: a horizontal fan for wide screens and a vertical fan for phones, so the
// phone layout is composed rather than squished.

export type FanService = {
  name: string;
  latencyMs?: number;
  cached?: boolean;
  /** Overrides the latency stamp with a different reading, such as a call count. */
  meta?: string;
};

export type FanNode = {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  labelX: number;
  labelY: number;
  metaX: number;
  metaY: number;
  boxed: boolean;
};

export type FanGeometry = {
  width: number;
  height: number;
  spine: { x1: number; y1: number; x2: number; y2: number };
  origin: { x: number; y: number };
  branches: { id: string; d: string; end: { x: number; y: number } }[];
  nodes: FanNode[];
  gathers: { id: string; d: string }[];
  envelope: {
    x: number;
    y: number;
    w: number;
    h: number;
    labelX: number;
    labelY: number;
    subX: number;
    subY: number;
  };
};

/** Wide screens: the spine on the left, branches peeling right into one envelope. */
export function horizontalLayout(services: FanService[]): FanGeometry {
  const width = 640;
  const height = 300;
  const spineX = 34;
  const originY = 150;
  const n = Math.max(services.length, 1);
  const spacing = n === 1 ? 0 : Math.min(72, 210 / (n - 1));

  const lanes = services.map((_, i) => originY + (i - (n - 1) / 2) * spacing);

  const branches = lanes.map((lane, i) => ({
    id: `branch-${i}`,
    d: `M${spineX},${originY} C120,${originY} 152,${lane} 208,${lane} L272,${lane}`,
    end: { x: 272, y: lane },
  }));

  const nodes: FanNode[] = services.map((s, i) => ({
    id: `node-${i}`,
    x: 278,
    y: lanes[i] - 17,
    w: 146,
    h: 34,
    labelX: 290,
    labelY: lanes[i] + 5,
    metaX: 412,
    metaY: lanes[i] + 5,
    boxed: true,
  }));

  const gathers = lanes.map((lane, i) => ({
    id: `gather-${i}`,
    d: `M428,${lane} L452,${lane} C476,${lane} 480,${originY} 506,${originY}`,
  }));

  return {
    width,
    height,
    spine: { x1: spineX, y1: 34, x2: spineX, y2: 266 },
    origin: { x: spineX, y: originY },
    branches,
    nodes,
    gathers,
    envelope: {
      x: 508,
      y: 110,
      w: 116,
      h: 80,
      labelX: 566,
      labelY: 144,
      subX: 566,
      subY: 164,
    },
  };
}

/** Phones: the spine stays on the left, the fan runs down, the envelope closes the page. */
export function verticalLayout(services: FanService[]): FanGeometry {
  const width = 340;
  const n = Math.max(services.length, 1);
  const laneGap = 56;
  const firstLane = 34;
  const envelopeTop = firstLane + laneGap * (n - 1) + 34;
  const height = envelopeTop + 62;

  const lanes = services.map((_, i) => firstLane + i * laneGap);

  const branches = lanes.map((lane, i) => ({
    id: `branch-${i}`,
    d: `M14,20 C14,${lane} 20,${lane} 34,${lane} L48,${lane}`,
    end: { x: 48, y: lane },
  }));

  const nodes: FanNode[] = services.map((s, i) => ({
    id: `node-${i}`,
    x: 60,
    y: lanes[i] - 8,
    w: 0,
    h: 0,
    labelX: 60,
    labelY: lanes[i] + 5,
    metaX: 336,
    metaY: lanes[i] + 5,
    boxed: false,
  }));

  const gathers = lanes.map((lane, i) => ({
    id: `gather-${i}`,
    d: `M${92 + i * 40},${lane + 9} L${92 + i * 40},${envelopeTop}`,
  }));

  return {
    width,
    height,
    spine: { x1: 14, y1: 20, x2: 14, y2: envelopeTop },
    origin: { x: 14, y: 20 },
    branches,
    nodes,
    gathers,
    envelope: {
      x: 16,
      y: envelopeTop,
      w: 308,
      h: 46,
      labelX: 32,
      labelY: envelopeTop + 21,
      subX: 308,
      subY: envelopeTop + 21,
    },
  };
}

export function layoutFor(
  services: FanService[],
  vertical: boolean
): FanGeometry {
  return vertical ? verticalLayout(services) : horizontalLayout(services);
}

export function formatLatency(ms?: number): string {
  if (ms === undefined || ms === null) return "";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
}
