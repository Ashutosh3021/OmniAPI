import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Roles, not hues. Stored as RGB triplets so opacity modifiers work.
        ground: "rgb(var(--rgb-ground) / <alpha-value>)",
        surface: "rgb(var(--rgb-surface) / <alpha-value>)",
        raised: "rgb(var(--rgb-raised) / <alpha-value>)",
        ink: "rgb(var(--rgb-ink) / <alpha-value>)",
        muted: "rgb(var(--rgb-muted) / <alpha-value>)",
        accent: "rgb(var(--rgb-accent) / <alpha-value>)",
        ok: "rgb(var(--rgb-ok) / <alpha-value>)",
        warn: "rgb(var(--rgb-warn) / <alpha-value>)",
        bad: "rgb(var(--rgb-bad) / <alpha-value>)",
        white: "#ffffff",
        black: "#000000",
      },
      spacing: {
        gutter: "var(--gutter)",
        page: "var(--pad-page)",
        rail: "var(--rail)",
      },
      fontFamily: {
        sans: ["var(--font-archivo)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        display: ["var(--t-display)", { lineHeight: "0.96", letterSpacing: "-0.038em" }],
        title: ["var(--t-title)", { lineHeight: "1.02", letterSpacing: "-0.028em" }],
        heading: ["var(--t-heading)", { lineHeight: "1.15", letterSpacing: "-0.018em" }],
        subhead: ["var(--t-subhead)", { lineHeight: "1.3", letterSpacing: "-0.008em" }],
        body: ["var(--t-body)", { lineHeight: "1.55" }],
        ui: ["var(--t-ui)", { lineHeight: "1.5" }],
        meta: ["var(--t-meta)", { lineHeight: "1.45" }],
        micro: ["var(--t-micro)", { lineHeight: "1.35" }],
      },
      // One radius rule for every rectangular surface on the site.
      borderRadius: {
        none: "0px",
        DEFAULT: "var(--radius)",
        sm: "var(--radius)",
        md: "var(--radius)",
        lg: "var(--radius)",
        xl: "var(--radius)",
        "2xl": "var(--radius)",
        "3xl": "var(--radius)",
        full: "9999px",
      },
      maxWidth: {
        prose: "68ch",
        shell: "1440px",
      },
    },
  },
  plugins: [],
};

export default config;
