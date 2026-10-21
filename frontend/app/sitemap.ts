import type { MetadataRoute } from "next";
import { site } from "@/lib/content/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const paths = ["/", "/docs", "/login", "/signup"];
  return paths.map((path) => ({
    url: `${site.url}${path}`,
    changeFrequency: path === "/" ? ("weekly" as const) : ("monthly" as const),
    priority: path === "/" ? 1 : 0.6,
  }));
}
