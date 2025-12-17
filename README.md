## Haki_FMCG - Intelligent RFP Response System

AI-powered platform for automated RFP processing, product matching, and response generation for the FMCG/Electrical industry.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm/yarn

### Installation & Launch

**Option 1: Automated Start (Recommended)**
```powershell
.\start_system.ps1
```

**Option 2: Manual Start**

**Backend:**
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**Frontend:**
```powershell
cd Frontend/tech
npm install
npm run dev
```

### Access Points
- Frontend Dashboard: http://localhost:5173
- Backend API: http://localhost:8002
- API Documentation: http://localhost:8002/docs

## System Overview

### Core Features
- RFP Discovery: Automated scanning from GeM, CPWD, and procurement portals
- AI Processing: Multi-agent system for requirement extraction and analysis
- Product Matching: Intelligent matching with OEM products
- Smart Pricing: Dynamic pricing engine with win probability analysis
- Document Generation: Automated PDF response generation
- Analytics Dashboard: Real-time KPIs and pipeline visualization

### Technology Stack
- Backend: FastAPI, SQLAlchemy, AsyncIO, SQLite
- Frontend: React 18, Vite, TailwindCSS
- AI/ML: Vector Embeddings, Semantic Search

## Architecture

### Backend Structure
```
backend/
├── main.py
├── api/
├── db/
├── services/
└── agents/

Frontend/
└── tech/
    └── src/
        ├── pages/
        ├── components/
        └── services/
```

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`

**Frontend errors:**
- Install dependencies: `npm install`
- Start dev server: `npm run dev`
Team Haki @ EY Techathon 6.0: Autonomous Multi-Agent AI for FMEG RFP automation. Streamlines tender identification, technical spec matching, pricing estimation, and bid document generation.
>>>>>>> origin/main
