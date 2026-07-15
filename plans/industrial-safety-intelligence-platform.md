# Industrial Safety Intelligence Platform — Construction Blueprint

**Objective:** Build a production-grade Industrial Safety Intelligence Platform for the hackathon with 6 core AI agents, real-time geospatial dashboard, RAG-powered incident intelligence, and automated compliance auditing.

---

## Project Context

**Existing Assets:**
- `backend/` — FastAPI + ChromaDB + Anthropic RAG engine (ingestion, query, knowledge graph)
- `intelliplant-ai/` — Extended backend with tests, frontend (React), ChromaDB persistence
- Python 3.11, FastAPI, Anthropic Claude, SentenceTransformers, ChromaDB

**Target Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TypeScript)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Live      │ │  Geospatial │ │  Incident   │ │  Permit &   │            │
│  │  Dashboard  │ │  Heatmap    │ │  Intelligence│ │  Compliance │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
└─────────┼────────────────┼────────────────┼────────────┼────────────────────┘
          │                │                │            │
          ▼                ▼                ▼            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  /risk       │ │  /heatmap    │ │  /incidents  │ │  /permits    │       │
│  │  /emergency  │ │  /compliance │ │  /audit      │ │  /kgraph     │       │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘       │
└─────────┼────────────────┼────────────────┼────────────┼────────────────────┘
          │                │                │            │
          ▼                ▼                ▼            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT ORCHESTRATION LAYER                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │ Compound Risk   │ │ Incident Pattern│ │ Permit Agent    │               │
│  │ Detection Engine│ │ Intelligence    │ │ (Approval/     │               │
│  │ (Multi-source   │ │ (RAG over       │ │  Compliance)   │               │
│  │  correlation)   │ │  incidents/regs)│ │                │               │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘               │
│           │                   │                   │                         │
│  ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐               │
│  │ Emergency       │ │ Quality/        │ │ Geospatial      │               │
│  │ Response        │ │ Compliance      │ │ Engine          │               │
│  │ Orchestrator    │ │ Audit Agent     │ │ (Heatmap/       │               │
│  │                 │ │                 │ │  Asset Tracker) │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  ChromaDB       │ │  PostgreSQL     │ │  Redis/         │
│  (Vector Store) │ │  (Relational:   │ │  Kafka (Real-   │
│  - Docs         │ │   Permits,      │ │   time: Sensor  │
│  - Incidents    │ │   Incidents,    │ │   streams,      │
│  - Regulations  │ │   Audits,       │ │   Alerts,       │
│  - Permits      │ │   Assets)       │ │   WebSocket)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Step 1: Foundation — Database Schema & Core Models

**Context:** Extend existing ChromaDB with PostgreSQL for relational data (permits, incidents, assets, audits, users). Create shared Pydantic/SQLAlchemy models.

**Files to Create/Modify:**
- `backend/models/__init__.py` — SQLAlchemy models
- `backend/models/schemas.py` — Pydantic request/response schemas
- `backend/database.py` — Async SQLAlchemy + ChromaDB connection pool
- `backend/config.py` — Centralized settings (Pydantic Settings)
- `alembic/` — Migration scripts

**Tasks:**
1. Create `backend/models/` with SQLAlchemy models: `PlantAsset`, `Permit`, `Incident`, `Audit`, `User`, `SensorReading`, `RiskZone`, `EmergencyProtocol`
2. Create `backend/schemas.py` with Pydantic models for all API contracts
3. Create `backend/database.py` with async engine, session factory, ChromaDB client
4. Create `backend/config.py` using `pydantic-settings` for env management
5. Initialize Alembic and create initial migration
6. Run migration and verify tables

**Verification:**
```bash
cd backend && alembic upgrade head
python -c "from models import *; print('Models OK')"
python -c "from database import engine; print('DB OK')"
```

**Exit Criteria:** All models import cleanly, migration runs, tables exist in PostgreSQL.

---

## Step 2: Compound Risk Detection Engine (Multi-Agent Correlation)

**Context:** Build the core correlation engine that fuses sensor streams, permit status, weather, maintenance logs, and shift rosters to detect compound risk scenarios (e.g., "Hot work permit + gas sensor spike + wind shift = CRITICAL").

**Files to Create:**
- `backend/agents/risk_engine/__init__.py`
- `backend/agents/risk_engine/correlation_engine.py` — Core correlation logic
- `backend/agents/risk_engine/data_fusion.py` — Multi-source ingestion
- `backend/agents/risk_engine/rules.py` — Configurable risk rules (YAML/JSON)
- `backend/agents/risk_engine/alert_dispatcher.py` — WebSocket + notification
- `backend/agents/risk_engine/schemas.py` — Risk event schemas
- `backend/api/risk.py` — REST endpoints

**Tasks:**
1. Define `RiskFactor` enum: `GAS_LEAK`, `HOT_WORK`, `CONFINED_SPACE`, `WEATHER_SHIFT`, `MAINTENANCE_OVERDUE`, `SHIFT_FATIGUE`, `PERMIT_CONFLICT`
2. Implement `DataFusionEngine` — ingests from Kafka/Redis streams (MQTT sensors, permit API, weather API, CMMS)
3. Implement `CorrelationEngine` — sliding window (5-min) correlation using rule engine + ML anomaly detection (IsolationForest)
4. Define risk rules in `rules/risk_rules.yaml` (e.g., `GAS_LEAK + HOT_WORK within 50m = CRITICAL`)
5. Implement `AlertDispatcher` — WebSocket broadcast, SMS/Email via Twilio/SendGrid, PagerDuty integration
6. Create REST endpoints: `GET /risk/current`, `GET /risk/history`, `WS /risk/stream`
7. Add unit tests with synthetic sensor streams

**Verification:**
```bash
cd backend && pytest agents/risk_engine/tests/ -v
curl localhost:8000/risk/current
# WebSocket test: wscat -c ws://localhost:8000/risk/stream
```

**Exit Criteria:** Engine correlates 5+ data sources, emits alerts < 2s latency, rules configurable without code change.

---

## Step 3: Geospatial Safety Heatmap Engine

**Context:** Real-time plant layout visualization with risk zones, asset tracking, and personnel location. WebSocket-driven updates from sensor fusion.

**Files to Create:**
- `backend/agents/geospatial/__init__.py`
- `backend/agents/geospatial/plant_layout.py` — SVG/GeoJSON layout loader
- `backend/agents/geospatial/heatmap_engine.py` — Risk interpolation (IDW/Kriging)
- `backend/agents/geospatial/asset_tracker.py` — BLE/GPS/RFID tag ingestion
- `backend/agents/geospatial/schemas.py` — GeoJSON FeatureCollection schemas
- `backend/api/heatmap.py` — REST + WebSocket endpoints
- `frontend/src/components/HeatmapView.tsx` — React-Leaflet/MapLibre component

**Tasks:**
1. Create plant layout schema (GeoJSON with zones: `process_unit`, `storage_tank`, `control_room`, `muster_point`, `fire_hydrant`)
2. Implement `HeatmapEngine` — Inverse Distance Weighting interpolation from sensor points to grid
3. Implement `AssetTracker` — consumes Kafka topic `asset.telemetry`, updates Redis geo-index (GEOADD)
4. Create `/heatmap/layout` (static GeoJSON), `/heatmap/live` (WebSocket stream), `/heatmap/history` (time-range query)
5. Build React component with MapLibre GL + deck.gl heatmap layer, real-time WebSocket subscription
6. Add zone click → drill-down to risk details, permit status, active incidents

**Verification:**
```bash
cd backend && pytest agents/geospatial/tests/ -v
cd frontend && npm test -- HeatmapView
# Manual: open frontend, verify live heatmap updates < 1s latency
```

**Exit Criteria:** 60fps map render, <500ms WebSocket→UI latency, zone click shows detail panel.

---

## Step 4: Incident Pattern Intelligence (RAG over Incidents/Regulations)

**Context:** Extend existing RAG engine to index incident reports, OSHA/ISO standards, root cause analyses, and near-miss narratives. Enable "Ask about similar incidents" and "What does API 581 say about this risk?"

**Files to Create/Modify:**
- `backend/agents/incident_intel/__init__.py`
- `backend/agents/incident_intel/ingestion.py` — PDF/HTML/CSV incident report parser
- `backend/agents/incident_intel/retrieval.py` — Hybrid search (vector + keyword + metadata filter)
- `backend/agents/incident_intel/analysis.py` — Root cause clustering, trend detection
- `backend/agents/incident_intel/schemas.py`
- `backend/api/incidents.py` — REST endpoints
- `frontend/src/components/IncidentIntel.tsx` — Chat + timeline UI

**Tasks:**
1. Extend ChromaDB collections: `incidents`, `regulations`, `root_causes`, `near_misses`
2. Build ingestion pipeline for: OSHA 300 logs, API standards (PDF), internal incident reports (PDF/Word), CSB reports
3. Implement hybrid retrieval: `sentence-transformers/all-MiniLM-L6-v2` + BM25 (via `rank_bm25`) + metadata filters (date, severity, equipment_type, unit)
4. Add `IncidentAnalystAgent` — LangChain/LangGraph agent with tools: `search_incidents`, `search_regulations`, `find_similar`, `extract_root_causes`
5. Endpoints: `POST /incidents/query`, `GET /incidents/trends`, `GET /incidents/similar/{incident_id}`
6. Frontend: Chat interface with citation cards, timeline visualization, "Similar Incidents" sidebar

**Verification:**
```bash
cd backend && pytest agents/incident_intel/tests/ -v
# Query test: curl -X POST localhost:8000/incidents/query -d '{"question": "similar incidents to pump seal failure"}'
```

**Exit Criteria:** Answers cite specific incidents/regulations, <3s latency, 90%+ citation accuracy on eval set.

---

## Step 5: Digital Permit Intelligence Agent

**Context:** Automate permit-to-work workflow: conflict detection, compliance validation, auto-approval for low-risk, escalation for high-risk. Integrate with risk engine for real-time permit suspension.

**Files to Create:**
- `backend/agents/permit/__init__.py`
- `backend/agents/permit/workflow_engine.py` — State machine (Draft → Review → Approved → Active → Closed)
- `backend/agents/permit/conflict_detector.py` — Spatial/temporal/resource conflicts
- `backend/agents/permit/compliance_checker.py` — Rule engine against regulations
- `backend/agents/permit/notification_service.py` — Approvers, stakeholders
- `backend/api/permits.py` — CRUD + workflow endpoints
- `frontend/src/components/PermitDashboard.tsx`

**Tasks:**
1. Define Permit model: `id`, `type` (hot_work, confined_space, working_at_height, excavation, electrical, line_break), `location`, `geometry`, `valid_from/to`, `status`, `approvers[]`, `conditions[]`, `linked_risk_assessment`
2. Implement `ConflictDetector` — checks: overlapping hot work + gas test, simultaneous confined space entries, permit vs. maintenance lockout (LOTO)
3. Implement `ComplianceChecker` — rules from `rules/permit_rules.yaml` (e.g., "Hot work requires gas test <30min old", "Confined space requires attendant")
4. Build workflow engine with async state transitions, audit trail, SLA timers
5. Integrate with Risk Engine: if risk score > threshold → auto-suspend permit, notify
6. Endpoints: `POST /permits`, `POST /permits/{id}/approve`, `POST /permits/{id}/suspend`, `GET /permits/active`, `WS /permits/stream`
7. Frontend: Kanban board (Draft/Review/Active/Closed), map view of active permits, conflict warnings

**Verification:**
```bash
cd backend && pytest agents/permit/tests/ -v
# Create permit via API, verify conflict detection triggers
```

**Exit Criteria:** Full permit lifecycle < 30s API latency, conflict detection 100% on test scenarios, audit trail immutable.

---

## Step 6: Emergency Response Orchestrator

**Context:** When incident declared, auto-generate response plan: muster rolls, resource allocation, evacuation routes, external agency notification, real-time tracker.

**Files to Create:**
- `backend/agents/emergency/__init__.py`
- `backend/agents/emergency/incident_commander.py` — Plan generation (ICS structure)
- `backend/agents/emergency/muster_manager.py` — Headcount via badge/RFID
- `backend/agents/emergency/resource_allocator.py` — Fire trucks, foam, medical, mutual aid
- `backend/agents/emergency/evacuation_router.py` — Dynamic routing on plant graph
- `backend/agents/emergency/external_notifier.py` — Mutual aid, 911, regulatory
- `backend/api/emergency.py`
- `frontend/src/components/EmergencyCommand.tsx`

**Tasks:**
1. Define `EmergencyIncident` model with ICS roles: IC, Safety Officer, Operations, Planning, Logistics, Liaison
2. Implement `IncidentCommander` agent — generates ICS-201/202/203/204 forms from plant layout + hazard data
3. `MusterManager` — consumes badge swipe/Kafka `personnel.location`, computes unaccounted personnel per muster point
4. `EvacuationRouter` — Dijkstra on plant graph (nodes=areas, edges=paths), weights = risk + congestion
4. `ResourceAllocator` — matches incident type/size to resource cache, auto-dispatches
5. `ExternalNotifier` — templates for mutual aid, NRC, OSHA, local FD; sends via webhook/email/SMS
6. Endpoints: `POST /emergency/declare`, `GET /emergency/{id}/plan`, `WS /emergency/{id}/tracker`
7. Frontend: Incident Command Dashboard — live map with responders, muster status, resource ETA, ICS forms

**Verification:**
```bash
cd backend && pytest agents/emergency/tests/ -v
# Simulate incident declaration, verify plan generated < 10s
```

**Exit Criteria:** Plan generated < 10s, muster accuracy > 99%, evacuation routes update < 2s on risk change.

---

## Step 7: Quality & Compliance Audit Agent

**Context:** Automated audit preparation: checklist generation, evidence collection, finding classification, corrective action tracking, regulatory submission package.

**Files to Create:**
- `backend/agents/audit/__init__.py`
- `backend/agents/audit/checklist_generator.py` — ISO 45001, OSHA PSM, API 580/581, Seveso
- `backend/agents/audit/evidence_collector.py` — Pulls from permits, inspections, training, maintenance
- `backend/agents/audit/finding_classifier.py` — ML classifier (Major/Minor/Obs)
- `backend/agents/audit/capa_tracker.py` — Corrective/Preventive Actions
- `backend/agents/audit/report_generator.py` — PDF/Word export
- `backend/api/audit.py`
- `frontend/src/components/AuditDashboard.tsx`

**Tasks:**
1. Define audit standards library (YAML): clauses → checklist items → evidence sources
2. `ChecklistGenerator` — maps standard + plant profile → tailored checklist
3. `EvidenceCollector` — queries permits, incidents, training records, calibration logs, MOC
4. `FindingClassifier` — fine-tuned DistilBERT on historical audit findings
5. `CAPATracker` — assigns owner, due date, verification, effectiveness check
6. `ReportGenerator` — Jinja2 → WeasyPrint PDF with evidence appendix
7. Endpoints: `POST /audits/prepare`, `GET /audits/{id}/checklist`, `POST /audits/{id}/findings`, `GET /audits/{id}/report`
8. Frontend: Audit prep dashboard, evidence gaps heatmap, CAPA board

**Verification:**
```bash
cd backend && pytest agents/audit/tests/ -v
# Generate audit for ISO 45001, verify checklist completeness
```

**Exit Criteria:** Checklist covers 100% of selected standard clauses, evidence auto-collection > 80%, report renders in < 30s.

---

## Step 8: Frontend — Unified Real-Time Dashboard

**Context:** Single-page React + TypeScript app with WebSocket connections to all agents. Role-based views (Operator, Supervisor, Safety Manager, Plant Manager).

**Files to Create/Modify:**
- `frontend/package.json` — Add: `@mantine/core`, `@tanstack/react-query`, `socket.io-client`, `maplibre-gl`, `deck.gl`, `recharts`, `zustand`
- `frontend/src/App.tsx` — Routing + auth context
- `frontend/src/components/` — All UI components
- `frontend/src/hooks/` — `useWebSocket`, `useRiskStream`, `useHeatmap`, `usePermits`
- `frontend/src/store/` — Zustand stores for each domain
- `frontend/src/pages/` — Dashboard, Risk, Heatmap, Incidents, Permits, Emergency, Audit, Settings
- `frontend/vite.config.ts`

**Tasks:**
1. Initialize Vite + React + TS + Mantine UI
2. Implement auth (JWT, role-based) — integrate with backend `/auth`
3. Build layout: Sidebar nav, top bar (live risk score, active permits, emergency button)
4. Implement WebSocket hook with auto-reconnect, heartbeat, message routing
5. Pages:
   - **Dashboard** — KPI cards, risk trend, active alerts, permit summary
   - **Risk Monitor** — Real-time risk factor table, correlation graph, alert history
   - **Heatmap** — Full-screen plant map with deck.gl layers
   - **Incident Intel** — Chat + citations + timeline
   - **Permits** — Kanban + map overlay + conflict panel
   - **Emergency** — ICS dashboard (only during active incident)
   - **Audit** — Checklist, evidence gaps, CAPA board
   - **Settings** — Plant layout editor, rule config, user management
6. Add E2E tests with Playwright

**Verification:**
```bash
cd frontend && npm run build && npm run test && npx playwright test
# Manual: Open 3 browser tabs (Operator/Supervisor/Manager), verify RBAC
```

**Exit Criteria:** Lighthouse > 90, all WebSocket streams live, RBAC enforced, responsive down to tablet.

---

## Step 9: Integration Testing, Observability & Demo Prep

**Context:** End-to-end verification, load testing, logging/metrics, architecture diagram, pitch deck, demo video.

**Files to Create:**
- `docker-compose.yml` — Full stack (Postgres, Redis, Kafka, Chroma, Backend, Frontend, Prometheus, Grafana)
- `backend/tests/integration/` — Cross-agent scenarios
- `docs/architecture.md` — Mermaid diagrams
- `docs/api.md` — OpenAPI spec
- `pitch_deck/` — Marp/Markdown slides
- `demo_script.md` — 5-min demo flow
- `Makefile` / `justfile` — Common commands

**Tasks:**
1. Write `docker-compose.yml` with all services, healthchecks, networks
2. Integration tests: Permit → Risk Engine → Heatmap → Emergency flow
3. Load test: 1000 concurrent WebSocket connections, 100 req/s API
4. Add structured logging (structlog), Prometheus metrics (`/metrics`), Grafana dashboards
5. Create architecture diagram (Mermaid → PNG)
6. Build pitch deck: Problem → Solution → Architecture → Demo → Business Case → Team
7. Record 5-min demo video (OBS + script)
8. Prepare hackathon submission: README, .env.example, deploy instructions

**Verification:**
```bash
docker-compose up -d && sleep 30
pytest backend/tests/integration/ -v
k6 run load_test.js
# Open Grafana, verify dashboards
```

**Exit Criteria:** All services healthy, integration tests pass, p99 < 500ms, demo video < 5 min.

---

## Parallelism Map

| Step | Depends On | Can Run Parallel With |
|------|------------|----------------------|
| 1 | — | — |
| 2 | 1 | 3, 4 |
| 3 | 1 | 2, 4 |
| 4 | 1 | 2, 3 |
| 5 | 1, 2 | 6, 7 |
| 6 | 1, 2, 3 | 5, 7 |
| 7 | 1, 4 | 5, 6 |
| 8 | 2, 3, 4, 5, 6, 7 | — |
| 9 | 8 | — |

**Critical Path:** 1 → 2 → 5 → 8 → 9 (or 1 → 3 → 8 → 9)

---

## Model Tier Assignment

| Step | Tier | Reason |
|------|------|--------|
| 1 | Default | Schema definition, boilerplate |
| 2 | **Strongest** | Core correlation logic, rule engine design |
| 3 | Strong | Geospatial algorithms, real-time viz |
| 4 | **Strongest** | RAG architecture, hybrid retrieval, agent design |
| 5 | Strong | Workflow engine, conflict detection |
| 6 | **Strongest** | Life-safety critical, ICS compliance |
| 7 | Strong | ML classifier, document generation |
| 8 | Default | UI implementation (well-defined specs) |
| 9 | Default | Ops, docs, video |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ChromaDB scaling | Pre-create collections, use persistent client, batch inserts |
| WebSocket scale | Redis pub/sub backend, connection pooling |
| LLM latency | Cache embeddings, use Haiku for classification, Sonnet for generation |
| Geospatial perf | Pre-compute heatmap tiles, Web Workers in frontend |
| Permit conflict false positives | Tunable rules, human-in-the-loop for CRITICAL |
| Emergency plan legal liability | Disclaimer: "Decision support only", audit trail immutable |
| Time | Parallelize Steps 2-4, 5-7; use existing backend as base |

---

## Definition of Done (Project Level)

- [ ] All 6 agents operational with APIs documented
- [ ] Frontend connects to all WebSocket streams
- [ ] Docker compose starts full stack in < 2 min
- [ ] Integration tests pass (CI green)
- [ ] Architecture diagram rendered
- [ ] Pitch deck < 15 slides, demo video < 5 min
- [ ] README with: quickstart, env vars, API docs, agent descriptions
- [ ] Submitted to hackathon before deadline