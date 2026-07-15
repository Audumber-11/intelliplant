# IntelliPlant — Deployment Guide

## 🚀 Quick Deploy

### Frontend ✅ (Already Deployed)

**URL:** https://frontend-9f4hdv98t-audumber-11s-projects.vercel.app  
**Alias:** https://frontend-eta-five-76.vercel.app  

> ⚠️ Frontend calls backend at `localhost:8000`. To connect live backend, update `frontend/src/api.ts`:
> ```ts
> const API_BASE = 'https://intelliplant-api.onrender.com'; // Replace localhost
> ```
> Then redeploy: `cd frontend && vercel --prod`

---

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `intelliplant`
3. Description: `AI-Powered Industrial Safety Intelligence Platform`
4. Visibility: **Public**
5. **DO NOT** initialize with README, .gitignore, or license
6. Click **Create repository**

### Step 2: Push Code to GitHub

Run these commands in your terminal:

```bash
cd "D:\ET hackthon"
git remote set-url origin https://github.com/Audumber-11/intelliplant.git
git push -u origin main
```

### Step 3: Deploy Backend to Render (Free Tier)

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub account
4. Select `Audumber-11/intelliplant`
5. Configure:
   - **Name:** `intelliplant-api`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** **Free**
6. Click **Create Web Service**
7. Wait for deploy (~5 min)

### Step 4: Update Frontend API URL

1. Edit `frontend/src/api.ts`
2. Change `http://localhost:8000` → `https://intelliplant-api.onrender.com`
3. Redeploy frontend:
   ```bash
   cd frontend
   vercel --prod --yes --scope audumber-11s-projects
   ```

### Step 5: Verify

- **Frontend:** https://frontend-eta-five-76.vercel.app
- **Backend Health:** https://intelliplant-api.onrender.com/health
- **API Docs:** https://intelliplant-api.onrender.com/docs

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🧪 Local Development

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Verification

Run full API test:
```bash
cd backend
python -m tests.verify
```

Expected: **18/18 endpoints PASS**

---

## 🌐 Architecture

```
Frontend (Vercel) ──HTTP──► Backend API (Render)
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
                 SQLite      ChromaDB     NetworkX
                 (data)     (vectors)     (graph)
```

---

## 📁 Project Structure

```
intelliplant/
├── backend/         # FastAPI backend with 10 AI agents
│   ├── agents/      # CCTV, IoT, KG, Orchestrator, etc.
│   ├── main.py      # 25+ API endpoints
│   ├── models/      # SQLAlchemy models
│   └── tests/       # Verification scripts
├── frontend/        # React/TypeScript SPA
│   ├── src/pages/   # 10 dashboard pages
│   └── src/api.ts   # API client
├── docs/            # PRD, Architecture, API docs
├── docker-compose.yml
├── vercel.json
└── render.yaml
```

---

## 🔗 Links

| Resource | URL |
|----------|-----|
| GitHub Repo | https://github.com/Audumber-11/intelliplant |
| Live Frontend | https://frontend-eta-five-76.vercel.app |
| Backend API | https://intelliplant-api.onrender.com |
| API Docs | https://intelliplant-api.onrender.com/docs |
| PRD | https://github.com/Audumber-11/intelliplant/blob/main/docs/PRD.md |
