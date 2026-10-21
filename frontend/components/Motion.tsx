"use client";

import { Engine } from "@/lib/engine/next";
import { setupMotion } from "@/lib/motion/setup";

export function Motion() {
  return <Engine setup={setupMotion} />;
}
