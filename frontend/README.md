# OmniAPI Frontend

Production-ready Next.js 14 application for the OmniAPI dashboard, converted from static HTML prototypes (desktop + mobile) into a unified responsive App Router experience.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React Hook Form** + **Zod** validation
- **Recharts** for analytics
- **Headless UI** for modals, drawers, menus
- **Lucide React** icons

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Demo Login

- **Email:** `alex@example.com`
- **Password:** `password123`

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/          # Login, signup, forgot password
│   ├── (dashboard)/     # Protected dashboard routes
│   └── api/             # Mock API route handlers
├── components/
│   ├── shared/          # Button, Input, Sidebar, etc.
│   ├── forms/           # Form components
│   ├── charts/          # Recharts wrappers
│   ├── tables/          # Data tables (responsive)
│   └── dashboard/       # Dashboard-specific widgets
├── context/             # Auth, Theme, Notifications
├── hooks/
├── lib/                 # API client, validators, mock data
└── types/
```

## Features

- Mobile-first responsive layout with collapsible sidebar drawer
- Dark / light theme toggle
- JWT-based auth with protected routes
- API Keys, External Services, Webhooks CRUD (mock backend)
- Analytics charts with CSV/JSON export
- API Orchestrate playground (send requests to `/api/*`)
- Documentation page with section navigation

## Scripts

| Command        | Description              |
|----------------|--------------------------|
| `npm run dev`  | Start development server |
| `npm run build`| Production build         |
| `npm run start`| Start production server  |
| `npm run lint` | Run ESLint               |

## Mock API

All data is served from in-memory mock stores in `lib/mockStore.ts`. Replace `lib/api.ts` calls with your real backend when ready.
