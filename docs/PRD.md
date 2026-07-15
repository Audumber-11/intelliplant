# IntelliPlant — AI-Powered Industrial Safety Intelligence Platform

**Product Requirements Document (PRD)**  
**Version:** 1.0.0  
**Status:** Draft  
**Author:** Audumber Shinde  
**GitHub:** [Audumber-11](https://github.com/Audumber-11)

---

## 1. Executive Summary

### 1.1 Problem Statement
Industrial facilities face critical challenges in safety management:
- **Fragmented data** — safety insights are scattered across CCTV feeds, IoT sensors, permit systems, incident logs, and audit reports with no unified view
- **Reactive response** — incidents are investigated after they occur rather than predicted and prevented
- **Manual analysis** — safety teams spend 60% of their time correlating data across disconnected systems
- **Compliance complexity** — regulatory standards (OISD-116, OSHA, IS 14489) require exhaustive documentation that is manually compiled
- **Slow emergency response** — average 8-12 minutes to detect and respond to critical events

### 1.2 Solution Overview
IntelliPlant is an **AI-powered multi-agent platform** that ingests data from CCTV, IoT/SCADA, permit systems, incident logs, and audit trails to provide:
- **Real-time compound risk detection** — cross-correlating inputs from all sources to identify emerging threats before escalation
- **Predictive analytics** — forecasting incident probability and severity using historical patterns and knowledge graph relationships
- **Automated compliance** — generating regulatory reports and audit trails with zero manual effort
- **Unified command center** — a single dashboard for safety intelligence, emergency response, and operational oversight

### 1.3 Target Users
| Role | Primary Need |
|------|-------------|
| **Safety Manager** | Real-time risk visibility, incident prevention, compliance reporting |
| **Plant Operator** | CCTV monitoring, IoT telemetry, permit validation |
| **Emergency Response Team** | Rapid situational awareness, muster management, response orchestration |
| **Compliance Officer** | Audit trails, regulatory checklist management, conformance scoring |
| **Executive** | Business impact metrics, trend analysis, ROI demonstration |

---

## 2. Product Vision

To become the **central nervous system for industrial safety** — an autonomous intelligence layer that predicts, prevents, and orchestrates responses to every safety event across the facility.

### 2.1 Strategic Goals
1. **Zero Harm Operations** — reduce workplace incidents by 80% through predictive prevention
2. **10x Efficiency** — eliminate manual data correlation and report generation
3. **Real-time Awareness** — sub-second detection-to-alert for all critical events
4. **Full Compliance Automation** — auto-generate OISD-116, OSHA, and IS 14489 reports

---

## 3. Features & Capabilities

### 3.1 Core Modules

#### P0 — Must Have (MVP)

| Module | Description |
|--------|------------|
| **Safety Dashboard** | KPI cards (active risks, open permits, incidents today, compliance score), risk distribution charts, real-time alerts feed |
| **Geospatial Heatmap** | IDW-interpolated risk heatmap over facility layout, zone-based filtering, personnel location tracking |
| **Incident Intelligence** | Incident CRUD with severity/status/category classification, pattern analysis with ML clustering |
| **Digital Permit Intelligence** | Permit lifecycle management, spatial-temporal conflict detection, risk assessment scoring |
| **Emergency Response Orchestrator** | Active emergency management, response time metrics, muster point planning with evacuation routes |
| **Quality & Compliance Audit** | Compliance scorecards, OISD-116/IS 14489 checklist engine, audit trail with major/minor/observation findings |

#### P1 — Advanced Modules

| Module | Description |
|--------|------------|
| **Computer Vision & CCTV Analytics** | PPE violation detection (helmets, vests, gloves), flame/smoke detection, unauthorized access detection, crowd gathering analysis, fall detection, gas leak visual indicators |
| **IoT / SCADA Integration** | Multi-protocol gateway (MQTT, OPC-UA, Modbus), real-time telemetry streaming, 9 sensor types (temperature, pressure, gas, vibration, humidity, flow, level, current, proximity) |
| **Knowledge Graph** | NetworkX-based graph with 10 node types and 13 edge types, risk propagation analysis, entity relationship mapping, path finding |
| **Agent Orchestrator** | LLM-powered reasoning with fallback, inter-agent message queue, background autonomous monitoring, decision logging |

### 3.2 Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| API Response Time | < 200ms (p95) |
| Dashboard Data Freshness | < 5 seconds |
| CCTV Detection Latency | < 2 seconds per frame |
| Knowledge Graph Query | < 500ms |
| Uptime | 99.5% |
| Concurrent Users | 50+ simultaneous |
| Data Retention | 1 year (incidents, permits, audits) |

---

## 4. Technical Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React SPA (Vite)                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────┐       │
│  │ Dash │ │Heat  │ │Inc   │ │ CCTV   │ │ IoT  │  ...   │
│  │board │ │ map  │ │idents│ │ Vision │ │SCADA │         │
│  └──────┘ └──────┘ └──────┘ └────────┘ └──────┘       │
│                        │  Axios HTTP                     │
├────────────────────────┼────────────────────────────────┤
│               FastAPI (Python 3.11+)                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Agent Orchestrator                   │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌───┐ ┌────────┐  │    │
│  │  │Risk  │ │Inc   │ │Permit│ │CV │ │ IoT/   │  │    │
│  │  │Engine│ │Intel │ │Agent │ │CCTV│ │ SCADA  │  │    │
│  │  └──────┘ └──────┘ └──────┘ └───┘ └────────┘  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │    │
│  │  │Knowledge │ │Compliance│ │ Emergency     │  │    │
│  │  │  Graph   │ │  Audit   │ │ Orchestrator  │  │    │
│  │  └──────────┘ └──────────┘ └───────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
│                        │                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SQLite       ChromaDB       Redis (optional)    │   │
│  │  (relational) (vector store) (cache/queue)       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | React 19, TypeScript, Vite, Recharts, Leaflet, Lucide Icons | Modern SPA with rich visualization |
| **Backend** | FastAPI, Python 3.11+ | Async-capable, auto-docs, Pydantic validation |
| **Database** | SQLAlchemy + SQLite (dev), PostgreSQL (prod) | ORM flexibility, easy dev setup |
| **Vector Store** | ChromaDB + Sentence Transformers | RAG for document intelligence |
| **AI Agents** | Claude API + mock fallback | LLM-powered reasoning and orchestration |
| **Computer Vision** | OpenCV | Real-time image/video processing |
| **Knowledge Graph** | NetworkX | Graph analysis, risk propagation |
| **IoT** | Paho-MQTT (simulated) | Multi-protocol sensor integration |

### 4.3 Data Flow

```
IoT Sensors ──► IoT Gateway ──► Agent Orchestrator ──► Knowledge Graph
CCTV Feeds ──► CV Engine   ──► Agent Orchestrator ──► Incident Intel
Permit Sys  ──► Permit Agent ──► Agent Orchestrator ──► Compliance Audit
                                                     ──► Dashboard
                                                     ──► Emergency Response
```

---

## 5. API Endpoints

### 5.1 Core Module Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/api/dashboard/kpis` | Dashboard KPI data |
| GET | `/api/heatmap/live` | Live geospatial heatmap |
| GET | `/api/incidents` | List incidents |
| POST | `/api/incidents` | Create incident |
| GET | `/api/permits` | List permits |
| GET | `/api/permits/conflicts` | Spatial-temporal conflicts |

### 5.2 Advanced Module Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cctv/summary` | CCTV cameras and detection summary |
| GET | `/api/cctv/alerts` | Active CV alerts |
| POST | `/api/cctv/alerts/{id}/acknowledge` | Acknowledge alert |
| GET | `/api/cctv/heatmap` | Alert-based detection heatmap |
| POST | `/api/cctv/process` | Trigger detection pipeline |
| GET | `/api/iot/metrics` | All IoT sensor metrics |
| GET | `/api/iot/devices` | Registered devices list |
| GET | `/api/iot/recent` | Recent telemetry stream |
| POST | `/api/iot/stream` | Stream batch data ingestion |
| GET | `/api/knowledge-graph/stats` | Graph statistics (nodes, edges) |
| GET | `/api/knowledge-graph/data` | Full graph data for visualization |
| GET | `/api/knowledge-graph/related/{id}` | Entity relationships |
| GET | `/api/knowledge-graph/risk-propagation` | Risk propagation paths |
| GET | `/api/knowledge-graph/paths` | Path finding between entities |
| GET | `/api/orchestrator/status` | System health and agent status |
| GET | `/api/orchestrator/decisions` | LLM decision log |
| POST | `/api/orchestrator/start` | Start autonomous monitoring |
| POST | `/api/orchestrator/stop` | Stop autonomous monitoring |
| GET | `/api/orchestrator/agents` | Agent fleet health metrics |

### 5.3 Total: 25+ API Endpoints

---

## 6. User Interface

### 6.1 Pages

| Route | Page | Components |
|-------|------|------------|
| `/` | Dashboard | KPI cards, risk charts, alert feed |
| `/heatmap` | Heatmap | Leaflet map, IDW overlay, zones |
| `/incidents` | Incidents | Table, pattern analysis |
| `/permits` | Permits | Table, conflict detection, risk scoring |
| `/emergency` | Emergency | Active emergencies, metrics, muster plan |
| `/audit` | Audit | Compliance score, OISD-116 checklist |
| `/cctv` | CCTV Vision | Camera grid, detection alerts, process feeds |
| `/iot` | IoT / SCADA | Protocol gateways, telemetry stream |
| `/knowledge-graph` | Knowledge Graph | Stats, entity explorer |
| `/orchestrator` | Orchestrator | Agent fleet, decision log, start/stop |

### 6.2 Design System
- **Theme:** Dark mode (#0f172a background, #1e293b cards)
- **Typography:** System font stack, monospace for data
- **Colors:** Amber (#f59e0b) for CTAs, emerald (#22c55e) for success, red (#ef4444) for alerts
- **Icons:** Lucide React icon library
- **Charts:** Recharts (bar, pie, area)

---

## 7. Deployment

### 7.1 Free Tier Deployment

| Service | Component | URL |
|---------|-----------|-----|
| **Vercel** | Frontend (React SPA) | `intelliplant.vercel.app` |
| **Render** | Backend (FastAPI) | `intelliplant-api.onrender.com` |

### 7.2 Local Development

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### 7.3 Docker

```bash
docker-compose up --build
```

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Incident reduction | 80% | MoM comparison |
| Detection-to-alert | < 2s | Backend logs |
| User adoption | 5+ departments | Active users/week |
| Compliance automation | 100% | Reports auto-generated |
| System uptime | 99.5% | Health check monitoring |

---

## 9. Roadmap

### Phase 1 — MVP (Current) ✅
- [x] Core safety dashboard with KPIs
- [x] Geospatial heatmap with IDW interpolation
- [x] Incident intelligence with pattern analysis
- [x] Digital permit intelligence with conflict detection
- [x] Emergency response orchestration
- [x] Compliance audit with OISD-116 checklist
- [x] Computer vision & CCTV analytics
- [x] IoT / SCADA integration
- [x] Knowledge graph with NetworkX
- [x] Multi-agent orchestrator with LLM reasoning

### Phase 2 — Production Hardening
- [ ] PostgreSQL database migration
- [ ] Redis caching layer
- [ ] Authentication & authorization
- [ ] Docker containerization
- [ ] CI/CD pipeline with GitHub Actions
- [ ] 80%+ test coverage

### Phase 3 — Scale
- [ ] Real CCTV camera integration (RTSP streams)
- [ ] Real MQTT/OPC-UA hardware integration
- [ ] Mobile app (React Native)
- [ ] Multi-facility support
- [ ] Enterprise SSO
- [ ] Custom report builder

---

## 10. Competitive Landscape

| Competitor | Our Advantage |
|-----------|--------------|
| **SAP EHS** | Real-time AI detection, unified platform, lower cost |
| **Sphera** | Open architecture, multi-agent AI, hackathon innovation |
| **Cority** | Computer vision integration, knowledge graph reasoning |
| **Legacy systems** | Modern UI, API-first, 10x faster deployment |

---

## 11. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mock data ≠ real data | High | Phased real-hardware integration |
| CV false positives | Medium | Confidence thresholds + human-in-loop |
| Backend cold starts (free tier) | Medium | Keep-alive pings every 5 min |
| API rate limits (LLM) | Low | Mock fallback + response caching |
| Database migration | Low | SQLAlchemy ORM abstracts differences |

---

## 12. Appendix

### 12.1 Glossary
- **IDW:** Inverse Distance Weighting (spatial interpolation)
- **OISD:** Oil Industry Safety Directorate
- **PPE:** Personal Protective Equipment
- **SCADA:** Supervisory Control and Data Acquisition
- **RAG:** Retrieval-Augmented Generation

### 12.2 References
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React 19 Documentation](https://react.dev/)
- [NetworkX Documentation](https://networkx.org/)
- [OISD-116 Standards](https://www.oisd.gov.in/)

---

*Built with Claude Code, FastAPI, React, and a lot of late-night engineering.*
