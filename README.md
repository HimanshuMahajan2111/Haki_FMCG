# Haki FMCG - Intelligent RFP Response System

AI-powered platform for automated RFP processing, product matching, and response generation for the FMCG/Electrical industry.

## 🚀 Quick Start

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
- **Frontend Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8002
- **API Documentation:** http://localhost:8002/docs

## 📋 System Overview

### Core Features
- **🔍 RFP Discovery:** Automated scanning from GeM, CPWD, and procurement portals
- **🤖 AI Processing:** Multi-agent system for requirement extraction and analysis
- **📦 Product Matching:** Intelligent matching with 50,000+ OEM products
- **💰 Smart Pricing:** Dynamic pricing engine with win probability analysis
- **📄 Document Generation:** Automated PDF response generation
- **📊 Analytics Dashboard:** Real-time KPIs and pipeline visualization

### Technology Stack
- **Backend:** FastAPI, SQLAlchemy, AsyncIO, SQLite
- **Frontend:** React 18, Vite, TailwindCSS, Lucide Icons
- **AI/ML:** OpenAI GPT-4, Vector Embeddings, Semantic Search
- **Database:** SQLite with async support

## 🏗️ Architecture

### Backend Structure
```
backend/
├── main.py                 # FastAPI application entry
├── api/
│   ├── routes/            # API endpoints
│   └── models.py          # Pydantic schemas
├── db/
│   ├── models.py          # SQLAlchemy models
│   └── database.py        # Database connection
├── services/
│   ├── data_service.py    # Product & pricing data
│   ├── rfp_service.py     # RFP processing logic
│   └── pricing_engine.py  # Pricing calculations
└── agents/                 # Multi-agent processors

Frontend/
└── tech/
    └── src/
        ├── pages/         # React page components
        ├── components/    # Reusable UI components
        └── services/      # API integration
```

## 💼 Key Workflows

### 1. RFP Processing Workflow
1. **Discovery** → Scan procurement portals
2. **Extraction** → Parse requirements with AI
3. **Matching** → Find suitable products
4. **Pricing** → Calculate competitive pricing
5. **Generation** → Create response document
6. **Submission** → Submit to customer

### 2. Product Management
- Add/Edit OEM products via Settings
- Bulk import from CSV files
- Real-time inventory sync
- Category & manufacturer filtering

### 3. Analytics & Reporting
- Pipeline value tracking
- Win rate analysis
- Response time metrics
- Stock health monitoring

## 🔧 Configuration

### Backend Settings
Edit `backend/main.py` for:
- API port configuration
- Database connection
- CORS settings
- OpenAI API keys

### Frontend Settings
Edit `Frontend/tech/vite.config.js` for:
- Development server port
- API proxy configuration
- Build optimization

## 📊 Database Schema

### Core Tables
- **rfps:** RFP records with status tracking
- **products:** OEM product catalog (50K+ items)
- **workflow_runs:** Processing history
- **agent_logs:** Multi-agent execution logs

## 🎯 Usage Guide

### Adding Products
1. Navigate to Settings → Products
2. Click "Add Product"
3. Fill product details (code, name, specs, pricing)
4. Submit to database

### Processing RFPs
1. Go to Enhanced Dashboard
2. View Live Lead Table
3. Click "Analyze" on any RFP
4. Monitor AI processing progress
5. Review matched products
6. Generate response PDF
7. Submit response

### Monitoring System
- **Dashboard:** Real-time KPIs and alerts
- **Processing Page:** Active workflow status
- **Analytics:** Historical performance trends
- **System Management:** Health checks and logs

## 🔐 Security Notes
- API endpoints require authentication (configure in production)
- Submission deadlines restricted to 2025-2026 range
- Input validation on all forms
- SQL injection protection via ORM

## 🐛 Troubleshooting

**Backend won't start:**
- Check Python version: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Verify port 8002 is available

**Frontend errors:**
- Clear node_modules: `rm -rf node_modules; npm install`
- Check Node version: `node --version`
- Verify backend is running on port 8002

**Database issues:**
- Delete `backend/haki_fmcg.db` to reset
- Run migrations: Database auto-creates on startup

## 📝 API Endpoints

### RFP Management
- `GET /api/rfp/latest` - Get recent RFPs
- `POST /api/rfp/submit` - Submit new RFP
- `GET /api/rfp/{id}` - Get RFP details
- `POST /api/rfp/{id}/submit` - Submit response

### Product Management
- `GET /api/products` - List products
- `POST /api/products/add` - Add product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard KPIs
- `GET /api/v1/analytics/pipeline` - Pipeline metrics

## 🚢 Deployment

**Production Checklist:**
- [ ] Set environment variables for API keys
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up authentication middleware
- [ ] Configure CORS for production domain
- [ ] Enable logging and monitoring
- [ ] Set up automated backups

## 📞 Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review application logs in `backend/logs/`
- Inspect browser console for frontend errors

## 📄 License

Proprietary - Haki FMCG Solutions

---

**Version:** 1.0.0  
**Last Updated:** December 2025  
**Status:** Production Ready

Proprietary and Confidential
