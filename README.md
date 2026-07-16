# IntelliPlant — AI-Powered Industrial Safety Intelligence

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **AI-powered multi-agent platform for zero-harm industrial operations.**  
> Predicts, detects, and orchestrates responses to safety events using Computer Vision, IoT/SCADA, Knowledge Graphs, and LLM-powered reasoning.

---

## ✨ Features

| Module | Capabilities |
|--------|-------------|
| **Safety Dashboard** | Real-time KPIs, risk distribution, live alerts |
| **Geospatial Heatmap** | IDW risk overlay, zone management, personnel tracking |
| **Incident Intelligence** | ML pattern analysis, severity classification, trend detection |
| **Permit Intelligence** | Digital permits, spatial-temporal conflict detection, risk scoring |
| **Emergency Response** | Active emergency management, muster planning, response metrics |
| **Compliance Audit** | OISD-116 checklist engine, compliance scoring, audit trails |
| **CCTV Vision** | AI detection: PPE, flame/smoke, unauthorized access, falls, gas leaks |
| **IoT / SCADA** | Multi-protocol (MQTT, OPC-UA, Modbus), live telemetry, 9 sensor types |
| **Knowledge Graph** | NetworkX: 62 nodes, 17 edge types, risk propagation, path finding |
| **Agent Orchestrator** | LLM-powered autonomous monitoring, inter-agent decision routing |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 React SPA (Vercel)                    │
├─────────────────────────────────────────────────────┤
│              FastAPI Backend (Render)                 │
│  ┌─────────┐ ┌─────────┐ ┌───────────────────────┐  │
│  │ Agents  │ │  API    │ │ Knowledge Graph       │  │
│  │ (9 AI)  │ │(25+ ep)│ │ NetworkX + ChromaDB   │  │
│  └─────────┘ └─────────┘ └───────────────────────┘  │
│              SQLite → PostgreSQL (prod)              │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
```

## 🧪 Testing

```bash
# API health check
curl http://localhost:8000/health

# Full verification
python backend/tests/verify.py
```

## 🌐 Live Demo

| Service | Component | URL |
|---------|-----------|-----|
| **Frontend** | React SPA | [https://frontend-eta-five-76.vercel.app](https://frontend-eta-five-76.vercel.app) |
| **Backend API** | FastAPI (local) | `http://localhost:8000` |
| **Demo Video** | Full walkthrough | [`screenshots/IntelliPlant_Full_Demo.mp4`](screenshots/IntelliPlant_Full_Demo.mp4) |
| **Screenshots** | 10 dashboard pages | [`screenshots/`](screenshots/) |

> **Backend Deployment:** To deploy the backend on Render free tier, click:  
> [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Audumber-11/intelliplant)

### 📸 Screenshots

| Dashboard | Heatmap | Incidents |
|:---------:|:-------:|:---------:|
| ![Dashboard](screenshots/01_Dashboard.png?raw=true) | ![Heatmap](screenshots/02_Heatmap.png?raw=true) | ![Incidents](screenshots/03_Incidents.png?raw=true) |
| **Permits** | **Emergency** | **Audit** |
| ![Permits](screenshots/04_Permits.png?raw=true) | ![Emergency](screenshots/05_Emergency.png?raw=true) | ![Audit](screenshots/06_Audit.png?raw=true) |
| **CCTV** | **IoT** | **Knowledge Graph** |
| ![CCTV](screenshots/07_CCTV.png?raw=true) | ![IoT](screenshots/08_IoT.png?raw=true) | ![KnowledgeGraph](screenshots/09_KnowledgeGraph.png?raw=true) |
| **Orchestrator** |
| ![Orchestrator](screenshots/10_Orchestrator.png?raw=true) |

## 📚 Documentation

- [Product Requirements Document](docs/PRD.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)

## 🛠️ Tech Stack

**Frontend:** React 19, TypeScript, Vite, Recharts, Leaflet, Lucide Icons  
**Backend:** FastAPI, Python 3.11+, SQLAlchemy, ChromaDB, NetworkX, OpenCV  
**AI/ML:** Claude API, Sentence Transformers, scikit-learn, Paho-MQTT  
**DevOps:** Docker, Vercel, Render, GitHub Actions

## 👤 Author

**Audumber**  
[GitHub](https://github.com/Audumber-11)

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

> *Built for innovation. Engineered for safety.*
