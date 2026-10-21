export const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  matchMedia("(prefers-reduced-motion: reduce)").matches;

export const isTouch = () =>
  typeof window !== "undefined" &&
  matchMedia("(hover: none), (pointer: coarse)").matches;

export const isMobile = () =>
  typeof window !== "undefined" && matchMedia("(max-width: 1023px)").matches;

/**
 * The shared easing vocabulary. One family, four named stops. Nothing in this
 * project may invent a curve of its own.
 */
export const ease = {
  out: "expo.out", // entrances
  inOut: "expo.inOut", // transitions
  soft: "power3.out", // small UI
  spring: "back.out(1.6)", // pops, used rarely
} as const;
