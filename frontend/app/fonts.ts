import { Archivo, JetBrains_Mono } from "next/font/google";

/**
 * One family carries display and text. The `wdth` axis is the concept hook:
 * display type is set wide (a fan opened), body type at normal width (a bundle
 * closed). The mono is the wire voice: branch labels, key prefixes, latencies.
 */
export const archivo = Archivo({
  subsets: ["latin"],
  axes: ["wdth"],
  variable: "--font-archivo",
  display: "swap",
});

export const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});
