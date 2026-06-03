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

[![Try OmniAPI](https://img.shields.io/badge/🚀_Launch_OmniAPI-005eff?style=for-the-badge&logo=rocket&logoColor=white&labelColor=000&color=0070f3)](https://omniapi3021.vercel.app)

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