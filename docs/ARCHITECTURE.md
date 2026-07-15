# IntelliPlant Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              React SPA (Vite + TypeScript)                  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────────┐  │  │
│  │  │Dashboard│ │Heatmap  │ │Incidents │ │ CCTV / IoT    │  │  │
│  │  │         │ │(Leaflet)│ │(Recharts)│ │ / KG / Orch   │  │  │
│  │  └─────────┘ └─────────┘ └──────────┘ └───────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP (Axios)
┌──────────────────────────▼───────────────────────────────────────┐
│                        API LAYER                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              FastAPI (Python 3.11+)                         │  │
│  │  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │  │
│  │  │ /health│ │ /api/inc │ │ /api/    │ │ /api/cctv   │   │  │
│  │  │        │ │ -idents  │ │ permits  │ │ /iot/kg/orch│   │  │
│  │  └────────┘ └──────────┘ └──────────┘ └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Risk     │ │  Incident  │ │  Permit    │ │  Compliance  │  │
│  │  Engine   │ │  Intel     │ │  Agent     │ │  Audit       │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  CV/CCTV  │ │  IoT/SCADA │ │ Knowledge  │ │ Orchestrator │  │
│  │  Agent    │ │  Gateway   │ │  Graph     │ │  (LLM)       │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │   SQLite     │ │   ChromaDB   │ │    NetworkX Graph        │  │
│  │  (SQLAlchemy)│ │ (Vector Store)│ │    (in-memory)           │  │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

Each agent follows the singleton pattern with a unified interface:

```python
class BaseAgent:
    async def initialize(self): ...
    async def shutdown(self): ...
    async def process(self, message: AgentMessage) -> AgentMessage: ...
```

### Agent Communication Flow

```
Orchestrator (LLM) ◄──► Risk Engine
     ◄──►     ◄──►         ◄──►
  Incident   Permit    Compliance
    Intel    Agent       Audit
     ◄──►     ◄──►         ◄──►
   CV/CCTV  IoT/SCADA  Knowledge
    Agent    Gateway      Graph
```

## Data Flow

### Real-time Detection Pipeline
```
IoT Sensor ──► Telemetry ──► Orchestrator ──► Risk Engine ──► KG Update ──► Dashboard
CCTV Feed  ──► CV Detect ──► Orchestrator ──► Alert        ──► Incident   ──► Dashboard
```

### Query Flow
```
User ──► React ──► Axios ──► FastAPI ──► Agent ──► DB/KG ──► Response ──► UI Update
```

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Monorepo** | Single repo for frontend + backend | Simpler dev setup, Atomic PRs |
| **SQLite dev → PostgreSQL prod** | Easy migration path | Zero config for dev, scalable for prod |
| **Mock data** | Realistic seed data | Demo-ready without real hardware |
| **Singleton agents** | Module-level globals | Stateful monitoring loops, low latency |
| **LLM fallback** | Mock mode API key not set | Demo works without paid API key |
