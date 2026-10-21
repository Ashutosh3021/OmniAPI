# OmniAPI — design system and build plan

Status: Phase 0–3 complete (refactor). QA / adjustment phase intentionally not started.

---

## Phase 0 — Brief

| | |
|---|---|
| **Subject** | OmniAPI, a self-hosted API gateway. You register third-party provider keys (weather, news, stock, …), mint one OmniAPI key, and call `POST /orchestrate` with a list of services. The gateway fans the call out in parallel, caches, retries and returns one envelope with a `results[]` array. |
| **Audience** | Backend developers who need one more third-party API in their product and do not want to own its auth, caching, rate limits or retries. |
| **Job of the site** | Get a developer to (1) understand in one screen that OmniAPI collapses N provider calls into one call, (2) create a key, (3) call `/orchestrate`. |
| **Assets provided** | None. The product is real (backend in `backend/`), the live API is `omniapi-api.onrender.com/api/v1`. |
| **Language** | English. |
| **Constraints** | Existing Next.js 14 App Router + Tailwind project with a working backend. The refactor must not change API contracts, auth flow, or routes. Frontend only. |

### Assumptions (invented, to be replaced)

- The hero fan diagram on `/` runs on **simulated** latencies and is labelled as such. It never claims to be live traffic.
- `/` becomes a public product landing page. The previous behaviour (redirect to `/login`) is replaced by a landing page that links to sign in; `/dashboard` stays behind `ProtectedRoute`.
- Billing numbers on the settings page (`Pro`, `5M calls`, `$99/month`) are placeholders already present in the code and stay flagged as placeholders.
- Product copy for the landing page describes only behaviour that exists in `backend/` (parallel fan-out, Redis cache, Celery refresh, rate-limit headers, webhook retries, JWT + `X-API-Key` auth).

---

## Phase 1 — Concept

Three candidates, one per territory.

| | A — *The fan* (process) | B — *The patch panel* (material) | C — *The manifest* (formal) |
|---|---|---|---|
| Idea | One request becomes a fan of parallel requests and gathers into one answer; the whole interface is drawn as that fan | Every service is a patched wire on a signal panel; calls are signals crossing it | Every response is a shipping manifest: one consignment note listing its compartments |
| Anchor | The literal API: `services: [...]` → `results: [...]`, each with `cache_hit` and `response_time_ms` | A gateway is literally a patch bay | The response envelope |
| Layout | A **spine** with branches | A rack of ports | A single column of form rows |
| Motion verb | fan out, hold, gather | patch, signal, blink | stamp, ship, close |
| Signature | The Fan: one spine, N branches, each returning at its own rate, converging into one envelope | A live port panel | A manifest that fills in |
| O / F / Fe / P | 4 / 5 / 5 / 2 | 3 / 3 / 4 / 3 | 3 / 3 / 3 / 4 |

**Picked: A — The fan.** It is the product itself rather than a metaphor laid over it: the
diagram a visitor sees on the landing page is literally the shape of the request the product
makes. It also generates the whole system rather than one effect: the spine becomes the page
grid, the branch labels become the type system (one variable width axis mirroring the fan
spread), the envelope becomes the response panel, and the empty state of a dead branch becomes
the 404.

Nothing from the worked examples in `references/concepts.md` is reused: there is no frame, no
viewport border, no running balance, no contact sheet, no mise en place, no code that compiles
into an image.

### Concept Card

```
Idea:        OmniAPI turns one call into a fan of parallel calls and gathers them into a
             single answer, so the whole interface is drawn as that fan.
Metaphor:    Signal routing on a patch panel. One spine carries the request, branches peel
             off to each provider, and the answers travel back and converge on one envelope.
Signature:   The Fan. An SVG diagram where a request leaves the spine, splits into one line
             per service, each line returns at its own rate, and all of them converge into a
             single response envelope. Built once (lib/motion/fan.ts) and reused at three
             scales: landing hero, Orchestrate result, sidebar branch ticks.
Emotion:     Precise and switched on. An instrument, not a landing page.
Motion verb: fan out, hold, gather.
Screenshot:  The landing hero: an ink spine on the left, three Klein-blue branches peeling
             right, a mono envelope on the right where they land.
```

### How the concept survives past the hero

- **Sidebar** — a vertical spine with a tick per destination; the active tick extends into a
  branch that meets the label.
- **Overview** — the fan diagram is the traffic breakdown, so the chart *is* the concept.
- **Orchestrate** — the response envelope is drawn, not printed.
- **Index lists** (keys, services, webhooks) — every row is a branch with a live/status lamp.
- **404** — a branch that dead-ends: "No route to this resource."
- **Empty states** — "Nothing patched here yet."

---

## Phase 2 — Art direction

Archetype: **tech precise / instrument**, executed as drafting paper rather than a dark neon
console. The reference is an engineering drawing on paper, not a screen in a dark room.

### Palette

Roles, not hues. Values below are the literal CSS custom properties in `app/globals.css`.

| Role | Light | Dark | Use |
|---|---|---|---|
| `ground` | `#F2F3F1` | `#0C0E12` | drafting sheet, page |
| `surface` | `#FFFFFF` | `#14171D` | raised panels, cards |
| `raised` | `#E8EAE6` | `#1C2028` | recessed: table heads, code, rails |
| `ink` | `#101318` | `#E9ECEF` | text, spine |
| `muted` | `#5A616B` | `#9AA3AE` | secondary text (AA both modes) |
| `line` | `rgba(16,19,24,.12)` | `rgba(233,236,239,.12)` | hairlines, the patch panel |
| `line-strong` | `rgba(16,19,24,.26)` | `rgba(233,236,239,.24)` | table rules, panel edges |
| `accent` | `#002FA7` | `#4C7DFF` | International Klein Blue: the live signal |
| `ok` | `#0E6B3F` | `#4FBF85` | panel LED, live fetch |
| `warn` | `#8A5A00` | `#E0A83C` | cache/pause states |
| `bad` | `#A8180F` | `#FF6B5E` | errors, revoked keys |
| `curtain` | `#101318` | `#101318` | transition sweep |

Why Klein blue: a real pigment, dense and technical, and it reads as a signal colour rather
than a brand gradient. It is used only where something is live or actionable. Status colours
are desaturated instrument LEDs, never neon.

Contrast (computed): ink/ground 16.5:1, muted/ground 5.6:1, accent/ground 10.7:1, white on
accent 10.7:1, ok/white 6.6:1, warn/white 5.9:1, bad/white 7.5:1, dark-mode accent/ground
5.2:1, dark muted/ground 7.6:1. All AA.

### Type

| Role | Family | Source | Setting |
|---|---|---|---|
| Display + text | **Archivo** (variable, `wdth` 62–125, `wght` 400–800) | Google via `next/font/google` | Display: `wdth 118`, `wght 700`, tracking `-0.035em`, leading `0.98`. Headings: `wdth 108`, `wght 600`. Body/UI: `wdth 100`, `wght 400–500`, 16–18 px, leading 1.5. |
| Data + labels | **JetBrains Mono** 400/500/600 | Google via `next/font/google` | 11–14 px, `wdth` n/a, tracking `0.02em`, uppercase only for panel labels at `0.08em`. `tabular-nums` everywhere a number moves. |

One family carries everything, and **the width axis is the concept**: display type is set
wide, like a fan opened; body type is set at normal width, like a bundle closed. The mono is
the wire voice: it labels branches, prefixes keys, stamps latencies.

Explicitly avoided: Inter, Fraunces, Instrument Serif, any serif, any script, any purple-blue
gradient, any eyebrow label above every heading.

### Fluid scale

```
--t-display: clamp(2.75rem, 1.35rem + 6.2vw, 6.5rem)
--t-h1:      clamp(2rem, 1.35rem + 2.9vw, 3.5rem)
--t-h2:      clamp(1.375rem, 1.12rem + 1.1vw, 1.875rem)
--t-h3:      clamp(1.0625rem, 0.99rem + 0.35vw, 1.25rem)
--t-body:    clamp(1rem, 0.965rem + 0.17vw, 1.0625rem)
--t-ui:      0.9375rem   (15px, dense UI)
--t-meta:    0.8125rem   (13px, panel labels)
--t-micro:   0.6875rem   (11px, mono stamps)
```

### Grid and rhythm

- Content: **12 columns**, gutter `clamp(16px, 2.2vw, 32px)`, outer margin = gutter.
- Fixed left rail 264 px at ≥1024 px; the rail is the **spine** of the whole app.
- **Alignment rule**: everything hangs from three vertical lines — the spine (col 1), a text
  line (col 4) and a data line (col 8). Section content starts on one of those three.
- Section rhythm has four moods, assigned deliberately, never constant: `tight` 16 px
  (inside panels), `normal` 28 px (between blocks), `airy` 64 px (between chapters),
  `full` 100 svh (one per site: the landing hero).
- **One layout family per section**, never repeated on a page: poster (hero), index list
  (keys/services/webhooks), asymmetric pair (overview), data/facts (metrics), sticky
  narrative (docs rail + content), full-bleed (code panel), footer-as-finale.

### Shape

**One radius rule: 4 px on every rectangular surface** (buttons, inputs, cards, badges, code
panels, menu). Status lamps are 6 px *dots*, a shape, not a radius. No pills, no 12 px
"card kit" radius. Corner radius is what makes a page read as a template; removing it is part
of the instrument idea.

### Motion language

- One easing family: `expo.out` (entrances), `power3.out` (micro UI), `expo.inOut`
  (transitions). No bespoke curves anywhere.
- Durations: micro 140 ms, element 260 ms, reveal 900 ms, page transition 620 ms.
- **Verb: fan out, hold, gather.**
  - Primary button: a Klein-blue fill floods up from the baseline while the label rolls up
    and a duplicate rolls in from below (the "inner text moves" mechanism, restyled).
  - Nav item: the spine tick extends into a branch and the label shifts 4 px right.
  - Table row: an accent rule draws in from the left edge.
  - Index row: the connector hairline draws from the spine to the row.
- **Idle:** the spine carries a slow travelling pulse (a 6 s dash-offset loop) and the landing
  fan keeps one signal running along it. Paused when the element is off screen, off entirely
  under reduced motion. This is the one thing on the site that moves with no input.
- Page transition: a **signal sweep** — a horizontal accent line crosses the viewport, the
  panel wipes across in the same direction, the new page's spine draws in. 620 ms, never
  blocking longer than the fetch.
- **No loader.** A developer tool has to be usable in under a second; a preloader would be
  pure latency. The landing hero composes on arrival with an intro timeline instead.

### Reveal + accessibility rules applied

- `data-split` only on server-rendered or static text (never text a client component
  re-renders).
- `data-reveal` blocks fade/rise; hidden-before-reveal is gated on `html.motion`, so the
  no-JS and reduced-motion pages are complete.
- Reduced motion: no smooth scroll, no reveals, no idle pulse, no transition sweep, no
  WebGL (there is none), and every piece of content visible.

### Genericness test

"If I gave a similar prompt to a generic model, would it land here?"

| Likely generic output | What this site does instead |
|---|---|
| Dark dashboard with neon grid / terminal green | Paper ground, Klein blue signal, drafting-sheet hairlines |
| "Features" trio of equal rounded cards | One layout family per section: index lists, data/facts, asymmetric pair, poster |
| Hero = centred headline over a gradient blob | Hero = a diagram of the actual request shape, left spine, asymmetric |
| Accent-on-everything rainbow service chips | One accent; services are distinguished by position, mono label and a status LED, never by hue |
| Inter everywhere | Archivo with the width axis as a concept hook |
| GitHub-stars-and-logo strip | No invented credentials; the demo is labelled simulated |
| Number cards in a 4-up grid | Metrics as a fan of three readings that converge on one envelope |
| Emoji in the feature list | None anywhere |

---

## Phase 3 — Build plan

**Stack: Next.js 14 App Router + Tailwind, unchanged.** The project already has a working
backend, auth, routes and data layer; the refactor changes the front end only and keeps the
framework the repo already runs on. GSAP + Lenis are added for the motion system.

### Engine (ported from `references/engine.md`, adapted)

```
lib/engine/env.ts           media queries + the shared easing names
lib/engine/scroll.ts        Lenis on the GSAP ticker
lib/engine/reveal.ts        data-split / data-reveal / data-parallax / data-intro
lib/engine/interactions.ts  data-magnetic
lib/engine/transition.ts    the signal sweep
lib/engine/index.ts         boot / leave / cleanup / enter / onPage
lib/engine/next.tsx         App Router adapter
lib/motion/setup.ts         global motion: transition + the fan driver
lib/motion/fan.ts           the concept driver (one variable → spine, branches, envelope)
```

No WebGL module: the concept is vector, the bundle stays small, and WPO is a scored row.
No loader module wiring: the loader is not used (decision above); the module is kept out of
the build entirely.

### Files

- **Foundation**: `app/globals.css` (tokens, engine CSS, site CSS), `tailwind.config.ts`
  (role-named tokens, fluid type), `app/fonts.ts`.
- **Shell**: `app/layout.tsx` (skip link, curtain, JSON-LD, metadata), `components/shell/*`
  (DashboardShell, SpineNav, TopBar, MobileNav).
- **Shared**: `components/shared/*` rewritten on the new tokens.
- **Signature**: `components/fan/FanDiagram.tsx` + `lib/motion/fan.ts`.
- **Landing**: `app/page.tsx`.
- **Auth**: `app/(auth)/*`.
- **Dashboard**: `app/(dashboard)/*` — overview, api-keys (+create,+detail), external services
  (+create,+detail), webhooks (+create,+detail), orchestrate, analytics, docs, settings.
- **Content**: `lib/content/site.ts` (product copy), `lib/content/docs.ts` (the documentation
  text, split out of the 748-line page file).
- **Meta**: `app/not-found.tsx`, `app/sitemap.ts`, `app/robots.ts`, `app/icon.svg`,
  `app/opengraph-image.tsx`.

### Signature moment — the Fan

`FanDiagram` is an SVG with a spine, N branch paths, a packet per branch and an envelope
target. States: `idle` → `fanning` (branches draw out, packets travel at rates derived from
each service's latency) → `holding` → `gathering` (branches converge into the envelope) →
`done`. The packet rides the path with GSAP MotionPathPlugin. Idle pulse is a dash-offset
loop on the spine.

Three placements:

1. **Landing hero** — large, auto-looping, simulated latencies, labelled `simulation`.
2. **Orchestrate page** — the same component, driven by the *real* response: service names,
   real `response_time_ms`, real `cache_hit`, real `success`.
3. **Sidebar** — a 2 px spine with a tick per destination; the active tick extends.

### Data honesty

- The landing fan is labelled `simulation` and shows invented service names and latencies.
- No invented customers, awards, uptime figures or call volumes anywhere.
- Billing figures on `/settings` are the pre-existing placeholders and stay flagged.
- Every screenshot-worthy number on the dashboard comes from the API; when the API is
  unavailable the page shows an empty state, never a fake number.

### QA (Phase 4) — not started

The QA loop, the critic pass and the adjustments are deliberately deferred until the user
says go. Nothing in this document claims a score.
