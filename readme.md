```
 ██████╗ ███╗   ███╗███╗   ██╗██╗ █████╗ ██████╗ ██╗
██╔═══██╗████╗ ████║████╗  ██║██║██╔══██╗██╔══██╗██║
██║   ██║██╔████╔██║██╔██╗ ██║██║███████║██████╔╝██║
██║   ██║██║╚██╔╝██║██║╚██╗██║██║██╔══██║██╔═══╝ ██║
╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║██║  ██║██║     ██║
 ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
```

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white&labelColor=000)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=000)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=for-the-badge&logo=postgresql&logoColor=white&labelColor=000)
![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=for-the-badge&logo=redis&logoColor=white&labelColor=000)
![Celery](https://img.shields.io/badge/Celery-5.3+-37B24D?style=for-the-badge&logo=celery&logoColor=white&labelColor=000)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white&labelColor=000)
![License](https://img.shields.io/badge/License-MIT-2ecc71?style=for-the-badge&logoColor=white&labelColor=000)
![Status](https://img.shields.io/badge/Status-V1%20Shipped-2ecc71?style=for-the-badge&logoColor=white&labelColor=000)

<div align="center">

[![Try OmniAPI](https://img.shields.io/badge/Launch_OmniAPI-005eff?style=for-the-badge&logo=rocket&logoColor=white&labelColor=000&color=0070f3)](https://omniapi3021.vercel.app)

</div>

---

## 🚀 Quick Summary

**OmniAPI** is a production-grade backend platform that lets users orchestrate calls to multiple external APIs through a single, intelligent interface. Instead of managing multiple API keys and hitting rate limits, users get **one API key from OmniAPI** and can intelligently call external services (weather, news, stocks, LLMs) with automatic **batching, caching, rate limiting, and async queuing**.

**Think of it as:** A smart traffic controller for API requests — making them faster, cheaper, and more reliable.

---

## 📋 The Problem

### Why Build This?
> - 🔑 **5+ API keys** scattered everywhere
> - ⚠️ **Rate limits** kill your workflow
> - 💰 **No caching** = wasted budget
> - 🐢 **Sequential calls** = slow responses
> - 👁️ **Zero visibility** into API usage
> - 🛠️ **Complex error handling** for each API
> - 🔒 **Blocking requests** tank performance

**Example Scenario:**
A SaaS product needs weather + news + stock data. Without OmniAPI:
- 3 different API keys to manage
- Hit rate limits independently
- Same data fetched 10x per hour = wasteful
- Calls happen sequentially = slow responses

---

## 🏗️ Architecture Overview

### System Design

```mermaid
graph TB
    %% Client layer
    subgraph Client_Layer
        WEB["🌐 Web Dashboard"]
        API_CLIENT["📱 User Applications"]
    end

    %% OmniAPI platform
    subgraph OmniAPI_Platform
        AUTH["🔐 Auth Layer\nJWT + OAuth2"]
        RATE["⏱️ Rate Limiter\nRedis"]
        CACHE["💾 Cache Layer\nRedis TTL"]
        QUEUE["📦 Job Queue\nCelery"]
        ORCHESTRATOR["🎯 API Orchestrator\nFastAPI"]
        WEBHOOK["🔔 Webhook Manager"]
        ANALYTICS["📊 Analytics Engine"]
    end

    %% Data layer
    subgraph Data_Layer
        DB["🗄️ PostgreSQL\nMulti-Tenant DB"]
        REDIS["⚡ Redis\nCache & Pub/Sub"]
    end

    %% External APIs
    subgraph External_APIs
        WEATHER["🌤️ OpenWeatherMap"]
        NEWS["📰 NewsAPI"]
        STOCK["📈 StockAPI"]
    end

    %% Deployment
    subgraph Deployment
        DOCKER["🐳 Docker Compose"]
        CI["🔄 GitHub Actions\nCI/CD"]
        RAILWAY["☁️ Railway/Render"]
    end

    WEB --> AUTH
    API_CLIENT --> AUTH
    AUTH --> ORCHESTRATOR
    ORCHESTRATOR --> RATE
    ORCHESTRATOR --> CACHE
    ORCHESTRATOR --> QUEUE
    ORCHESTRATOR --> WEBHOOK
    ORCHESTRATOR --> ANALYTICS
    RATE --> DB
    CACHE --> REDIS
    QUEUE --> REDIS
    ORCHESTRATOR --> WEATHER
    ORCHESTRATOR --> NEWS
    ORCHESTRATOR --> STOCK
    DB --> DOCKER
    REDIS --> DOCKER
    DOCKER --> CI
    CI --> RAILWAY

    style AUTH fill:#ff9999
    style RATE fill:#99ccff
    style CACHE fill:#99ff99
    style QUEUE fill:#ffcc99
    style ORCHESTRATOR fill:#ff99ff
```

---

## 🔑 How It Works (User Perspective)

### Workflow Diagram

```mermaid
sequenceDiagram
    actor User
    participant Dashboard as OmniAPI Dashboard
    participant Platform as OmniAPI Platform
    participant Cache as Cache Layer
    participant Queue as Job Queue
    participant ExtAPI as External APIs

    User->>Dashboard: 1. Sign up & Create API Key
    User->>Dashboard: 2. Add external API keys<br/>(Weather, News, Stock)
    User->>Platform: 3. Call OmniAPI using key<br/>GET /orchestrate?services=weather,news
    Platform->>Cache: Check if data cached
    alt Cache Hit
        Cache-->>Platform: Return cached data (instant)
    else Cache Miss
        Platform->>Queue: Queue external API calls
        Queue->>ExtAPI: Fetch from external APIs<br/>(async, parallel)
        ExtAPI-->>Queue: Return data
        Queue->>Cache: Store result with TTL
        Queue-->>Platform: Return data
    end
    Platform-->>User: Fast response with batched data
    User->>Dashboard: 4. View usage analytics<br/>(API calls, cached hits, cost saved)
```

---

## 👤 User Workflow

End-to-end guide — from signing up to making real orchestrated calls from your own application.

### Step 1 — Create an Account

Go to [omniapi3021.vercel.app](https://omniapi3021.vercel.app) and register.

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "full_name": "Jane Smith",
  "email": "jane@example.com",
  "password": "yourpassword"
}
```

Then log in to get your JWT token pair:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "jane@example.com",
  "password": "yourpassword"
}
```

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

Use `access_token` as a `Bearer` token for all dashboard API calls. The dashboard refreshes it automatically via `POST /api/v1/auth/refresh` when it expires.

---

### Step 2 — Add Your External API Keys

OmniAPI calls third-party services **using your own API keys** for those providers. You register them once under External Services — they are AES-encrypted at rest and never returned in any response.

In the dashboard go to **External Services → Add Service**, or call:

```http
POST /api/v1/external-services
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service_name": "weather",
  "api_key": "your_openweathermap_key",
  "max_calls_per_hour": 100
}
```

Repeat for each service. Supported `service_name` values:

| Value | Provider | Get a key at |
|---|---|---|
| `weather` | OpenWeatherMap | [openweathermap.org/api](https://openweathermap.org/api) |
| `news` | NewsAPI | [newsapi.org](https://newsapi.org) |
| `stock` | StockAPI | your stock data provider |

**List configured services:**

```http
GET /api/v1/external-services
Authorization: Bearer <access_token>
```

```json
[
  {
    "service_id": 1,
    "service_name": "weather",
    "max_calls_per_hour": 100,
    "status": "active",
    "created_at": "2026-06-03T10:00:00Z"
  }
]
```

A service must be in `active` status before it can be orchestrated. You can pause it with `PATCH /api/v1/external-services/{id}` by setting `"status": "inactive"`, or remove it entirely with `DELETE /api/v1/external-services/{id}`.

---

### Step 3 — Generate an OmniAPI Key

Generate the key your **application** uses to authenticate with OmniAPI. In the dashboard go to **API Keys → Create Key**, or call:

```http
POST /api/v1/api-keys
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Production App",
  "expires_at": "2027-01-01T00:00:00Z"
}
```

```json
{
  "key_id": 3,
  "name": "Production App",
  "raw_key": "omni_xK9mP2qL...",
  "is_active": true,
  "expires_at": "2027-01-01T00:00:00Z",
  "created_at": "2026-06-03T10:05:00Z"
}
```

> **`raw_key` is shown once only.** Copy it immediately and store it in your app's environment variables. It cannot be retrieved again.

Your application passes this key in the `X-API-Key` header on every orchestrate call.

---

### Step 4 — Make Orchestrated Calls

Send a single POST with the list of services you want and any per-service params. OmniAPI fans the calls out in parallel via Celery, caches results in Redis, and returns everything together.

```http
POST /api/v1/orchestrate
X-API-Key: omni_xK9mP2qL...
Content-Type: application/json

{
  "services": ["weather", "news"],
  "params": {
    "weather": { "city": "London" },
    "news":    { "q": "technology", "pageSize": 5 }
  }
}
```

```json
{
  "request_id": "a1b2c3d4-...",
  "total_time_ms": 312,
  "timestamp": "2026-06-03T10:10:00Z",
  "results": [
    {
      "service": "weather",
      "success": true,
      "cache_hit": false,
      "response_time_ms": 287,
      "data": { "city": "London", "temp_c": 18.4, "condition": "Partly cloudy" }
    },
    {
      "service": "news",
      "success": true,
      "cache_hit": true,
      "response_time_ms": 0,
      "data": { "articles": [ "..." ] }
    }
  ]
}
```

What to notice:

- `cache_hit: true` on `news` → served from Redis instantly, no external call made
- `cache_hit: false` on `weather` → fresh Celery task was dispatched and awaited
- `X-RateLimit-Remaining` response header tells you calls remaining in the current window
- A failed service returns `"success": false` with an `"error"` string; other services in the same request are unaffected
- Results are always ordered to match your `services` array

**Single-service call** — same shape, one item in `services`:

```json
{ "services": ["stock"], "params": { "stock": { "symbol": "AAPL" } } }
```

You can also authenticate with a `Bearer` JWT instead of `X-API-Key` when calling from a trusted server context.

---

### Step 5 — Monitor Usage in Analytics

Every orchestrated call is logged automatically. The **Analytics** page in the dashboard shows calls, cache hit rate, response times, and per-service breakdowns.

```http
GET /api/v1/analytics/summary
Authorization: Bearer <access_token>
```

```json
{
  "calls_today": 1420,
  "calls_change": 12.5,
  "cache_hit_percent": 67.3,
  "avg_response_ms": 184.0,
  "response_change_ms": -22.0
}
```

```http
GET /api/v1/analytics/usage?period=last_7d
Authorization: Bearer <access_token>
```

Valid `period` values: `last_24h` · `last_7d` · `last_30d`

Download a CSV report of the last 30 days:

```http
GET /api/v1/analytics/reports
Authorization: Bearer <access_token>
```

---

### Step 6 — Set Up Webhooks (Optional)

Subscribe to real-time events so your system reacts to orchestration outcomes without polling.

```http
POST /api/v1/webhooks
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "url": "https://yourapp.com/hooks/omniapi",
  "event_type": "orchestrate.complete"
}
```

```json
{
  "webhook_id": 7,
  "url": "https://yourapp.com/hooks/omniapi",
  "event_type": "orchestrate.complete",
  "is_active": true,
  "retry_count": 0,
  "secret": "a3f9bc...",
  "created_at": "2026-06-03T10:15:00Z"
}
```

> **`secret` is shown once only.** Use it to verify the `X-OmniAPI-Signature` header on incoming payloads.

**Supported event types:**

| Event | Fires when |
|---|---|
| `orchestrate.complete` | All services in a request succeeded |
| `orchestrate.failed` | One or more services failed |
| `api_key.created` | A new OmniAPI key was generated |

**Payload your endpoint receives:**

```json
{
  "event_id": "uuid",
  "event_type": "orchestrate.complete",
  "tenant_id": "42",
  "timestamp": "2026-06-03T10:10:05Z",
  "data": {
    "request_id": "a1b2c3d4-...",
    "services": ["weather", "news"],
    "total_time_ms": 312,
    "results_summary": [
      { "service": "weather", "success": true,  "cache_hit": false },
      { "service": "news",    "success": true,  "cache_hit": true  }
    ]
  }
}
```

OmniAPI retries failed deliveries automatically. Check delivery history:

```http
GET /api/v1/webhooks/{webhook_id}
Authorization: Bearer <access_token>
```

Send a test ping to verify your endpoint is reachable:

```http
POST /api/v1/webhooks/{webhook_id}/test
Authorization: Bearer <access_token>
```

---

### Step 7 — Manage & Rotate Keys

**List all keys:**

```http
GET /api/v1/api-keys
Authorization: Bearer <access_token>
```

**Update a key's name or expiry:**

```http
PATCH /api/v1/api-keys/{key_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Production App v2",
  "expires_at": "2028-01-01T00:00:00Z"
}
```

**Permanently delete a key** (any app using it gets `401` immediately):

```http
DELETE /api/v1/api-keys/{key_id}
Authorization: Bearer <access_token>
```

For zero-downtime rotation: create the new key → update your app env var → delete the old key.

---

### Full Workflow at a Glance
```mermaid
flowchart TD
    subgraph Setup["🚀 Setup"]
        A([Sign Up / Log In]) --> B[Configure Services<br/>weather · news · stock]
        B --> C[Get API Key<br/>omni_xxx...]
    end
    
    subgraph Request["⚡ Request Flow"]
        D[Your App Sends Request<br/>X-API-Key: omni_xxx] --> E{Cache Hit?}
        E -->|✅ Yes| G["⚡ Return Instantly<br/>cache_hit: true"]
        E -->|❌ No| H[Dispatch Parallel Tasks<br/>Celery]
        H --> I["🔄 Call External APIs<br/>in Parallel"]
        I --> J["💾 Cache Results<br/>Redis TTL"]
        J --> K[Return Response]
    end
    
    subgraph Notify["📊 Post-Processing"]
        G --> L[Log Usage]
        K --> L
        L --> M["🔔 Fire Webhook<br/>orchestrate.complete"]
        L --> N[Update Analytics]
    end
    
    M --> O([📈 Dashboard])
    N --> O
    
    style Setup fill:#6366f1,stroke:#000,color:#fff
    style Request fill:#0070f3,stroke:#000,color:#fff
    style Notify fill:#005eff,stroke:#000,color:#fff
```
---

## 💡 Key Design Decisions

### Decision 1: Multi-Tenant Architecture

**Problem:** How to safely serve multiple users without data leakage?

```
┌─────────────────┬──────────────────┐
│ DECISION        │ Multi-Tenant DB  │
├─────────────────┼──────────────────┤
│ TRADEOFF        │ More complex     │
│                 │ queries with     │
│                 │ tenant filtering │
├─────────────────┼──────────────────┤
│ RESULT          │ ✅ Scalable      │
│                 │ ✅ Cost-efficient│
│                 │ ✅ Data isolated │
└─────────────────┴──────────────────┘
```

**Implementation:**
- Every table has `tenant_id` foreign key
- Row-level security enforced in queries
- Tenants never see each other's data

---

### Decision 2: Redis for Caching + Rate Limiting

**Problem:** How to handle 1000s of requests/second without melting the database?

```
┌──────────────────┬──────────────────────┐
│ DECISION         │ Redis (In-Memory)    │
├──────────────────┼──────────────────────┤
│ TRADEOFF         │ Data lost on crash   │
│                  │ (but OK for cache)   │
├──────────────────┼──────────────────────┤
│ RESULT           │ ✅ Sub-millisecond   │
│                  │ ✅ Handles millions  │
│                  │ ✅ Perfect for TTL   │
└──────────────────┴──────────────────────┘
```

**What Redis Does:**
- **Rate Limiting:** "User A: 95/100 calls remaining"
- **Caching:** "Weather data expires in 1 hour"
- **Pub/Sub:** Real-time webhook events

---

### Decision 3: Celery for Async Jobs

**Problem:** Calling slow external APIs blocks responses for 5-10 seconds.

```
┌──────────────────┬──────────────────────┐
│ DECISION         │ Celery Task Queue    │
├──────────────────┼──────────────────────┤
│ TRADEOFF         │ More infrastructure  │
│                  │ (Celery + Redis)     │
├──────────────────┼──────────────────────┤
│ RESULT           │ ✅ Instant responses │
│                  │ ✅ No blocking calls │
│                  │ ✅ Retries + recovery
└──────────────────┴──────────────────────┘
```

**How It Works:**
```
User Request → Queue Job → Return Immediately → Process in Background
```

---

### Decision 4: PostgreSQL for Relational Data

**Problem:** Need to store users, API keys, external services, usage logs — all interconnected.

```
┌──────────────────┬──────────────────────┐
│ DECISION         │ PostgreSQL (SQL DB)  │
├──────────────────┼──────────────────────┤
│ TRADEOFF         │ Slower than NoSQL    │
│                  │ for simple reads     │
├──────────────────┼──────────────────────┤
│ RESULT           │ ✅ ACID guarantees   │
│                  │ ✅ Complex queries   │
│                  │ ✅ Data integrity    │
└──────────────────┴──────────────────────┘
```

---

## 📊 Data Models (Simplified)

```mermaid
erDiagram
    USER {
        int user_id PK
        string email
        string password_hash
        string tier
        timestamp created_at
    }

    API_KEY {
        int key_id PK
        int user_id FK
        string key_hash
        string name
        timestamp expires_at
        boolean is_active
    }

    EXTERNAL_SERVICE {
        int service_id PK
        int user_id FK
        string service_name
        string api_key_encrypted
        int max_calls_per_hour
        string status
    }

    USAGE_LOG {
        int log_id PK
        int user_id FK
        int service_id FK
        int response_time_ms
        boolean cache_hit
        timestamp created_at
    }

    WEBHOOK {
        int webhook_id PK
        int user_id FK
        string event_type
        string url
        int retry_count
    }

    USER ||--o{ API_KEY : has
    USER ||--o{ EXTERNAL_SERVICE : owns
    USER ||--o{ USAGE_LOG : generates
    USER ||--o{ WEBHOOK : subscribes
    EXTERNAL_SERVICE ||--o{ USAGE_LOG : logs
```

---

## 🛠️ Tech Stack Deep Dive

| Component | Technology | Why This Choice |
|-----------|------------|-----------------|
| **Backend Framework** | FastAPI | Async-first, auto-docs, blazing fast |
| **Database** | PostgreSQL | ACID, relational data, proven at scale |
| **Cache/Queue Broker** | Redis | Sub-millisecond speed, pub/sub support |
| **Job Queue** | Celery | Distributed tasks, retries, scheduling |
| **ORM** | SQLAlchemy | Type hints, migration support, flexibility |
| **Auth** | JWT + OAuth2 | Stateless, industry standard |
| **Testing** | pytest | Fast, fixtures, 80%+ coverage goal |
| **Containerization** | Docker Compose | Dev/prod parity, easy scaling |
| **CI/CD** | GitHub Actions | Free, integrated with repos |
| **Deployment** | Railway/Render | Free tier, auto-scaling, painless |
---

## 🚀 Getting Started

### Prerequisites
```bash
✅ Python 3.11+
✅ Docker & Docker Compose
✅ PostgreSQL 15+
✅ Redis 7+
```