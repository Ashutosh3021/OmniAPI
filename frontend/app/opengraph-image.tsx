import { ImageResponse } from "next/og";
import { site } from "@/lib/content/site";

export const runtime = "edge";
export const alt = `${site.name}: one call for every third-party API`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#F2F3F1",
          color: "#101318",
          padding: "72px",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <svg width="40" height="40" viewBox="0 0 18 18" fill="none">
            <path
              d="M3 1.5v15"
              stroke="#101318"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <path
              d="M3 4.5h4.5M3 9h6.5M3 13.5h4.5"
              stroke="#101318"
              strokeWidth="1.25"
              strokeLinecap="round"
              opacity="0.55"
            />
            <circle cx="3" cy="9" r="2.1" fill="#002FA7" />
          </svg>
          <div style={{ fontSize: "30px", fontWeight: 700, letterSpacing: "-0.5px" }}>
            OmniAPI
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              fontSize: "84px",
              lineHeight: 1.02,
              letterSpacing: "-3px",
              fontWeight: 700,
            }}
          >
            One call fans out.
          </div>
          <div
            style={{
              fontSize: "84px",
              lineHeight: 1.02,
              letterSpacing: "-3px",
              fontWeight: 700,
              color: "#002FA7",
            }}
          >
            Many answers gather back.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "20px",
            fontSize: "26px",
            color: "#5A616B",
          }}
        >
          <span>Parallel fan-out</span>
          <span style={{ color: "#5A616B" }}>|</span>
          <span>Caching</span>
          <span style={{ color: "#5A616B" }}>|</span>
          <span>One signed response</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
