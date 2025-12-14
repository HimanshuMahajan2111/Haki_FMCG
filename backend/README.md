# RFP Response System - Backend

AI-Powered Multi-Agent System for B2B RFP Response Automation

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The RFP Response System is an intelligent backend service that automates the process of responding to B2B Request for Proposals (RFPs) using a multi-agent AI architecture. It leverages large language models (LLMs) to analyze RFP requirements, match products from a database of 2,500+ electrical products, check compliance with industry standards, and generate competitive pricing.

### Key Capabilities

- **Automated RFP Processing**: Scans directories for new RFP PDFs and processes them automatically
- **Semantic Product Matching**: Uses vector embeddings to find the best matching products
- **Standards Compliance**: Validates products against IS/IEC standards
- **Intelligent Pricing**: Calculates pricing with volume discounts, testing costs, and taxes
- **Multi-Agent Orchestration**: Technical and Pricing agents work in parallel for efficiency
- **RESTful API**: Complete FastAPI backend with async support

---

## ✨ Features

### AI & Machine Learning
- ✅ OpenAI GPT-4 & Anthropic Claude integration
- ✅ LangChain for agent orchestration
- ✅ ChromaDB vector database for semantic search
- ✅ Sentence transformers for embeddings

### Architecture
- ✅ Async/await throughout (FastAPI, SQLAlchemy)
- ✅ Parallel agent execution for 2x performance
- ✅ Automatic retry with exponential backoff
- ✅ Structured logging with contextual information

### Data Management
- ✅ PostgreSQL/SQLite database support
- ✅ 2,500+ FMEG products (Havells, Polycab, etc.)
- ✅ 600+ wires & cables data
- ✅ 24 industry standards (IS/IEC)
- ✅ 63 testing procedures

---

## 📦 Prerequisites

### Required Software
- **Python**: 3.10 or higher (tested on 3.13)
- **Database**: PostgreSQL 14+ (production) or SQLite (development)
- **Redis**: Optional, for caching

### API Keys
- **OpenAI API Key**: Required for GPT-4 models
- **Anthropic API Key**: Optional, for Claude models

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 5GB free space
- **OS**: Windows, Linux, or macOS

---

## 🚀 Installation

### Step 1: Clone and Navigate

```bash
cd d:\Haki_FMCG\backend
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

**Option A: Production (with PostgreSQL)**
```bash
pip install -r requirements.txt
```

**Option B: Development (with SQLite)**
```bash
pip install -r requirements-dev.txt
```

### Step 4: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env file with your configuration
# Required: DATABASE_URL, OPENAI_API_KEY, SECRET_KEY
```

### Step 5: Initialize Database

```bash
# Create tables and load product data
python scripts/init_db.py
```

---

## ⚙️ Configuration

### Environment Variables

Edit the `.env` file with your settings:

#### Application Settings
```env
API_HOST=0.0.0.0          # API host
API_PORT=8000              # API port
ENVIRONMENT=development    # Environment mode
DEBUG=True                 # Debug mode
```

#### Database Configuration
```env
# For PostgreSQL (Production)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/rfp_system

# For SQLite (Development)
DATABASE_URL=sqlite+aiosqlite:///./rfp_system.db
```

#### AI Model Configuration
```env
OPENAI_API_KEY=sk-...                    # Your OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...             # Your Anthropic API key
DEFAULT_LLM_MODEL=gpt-4-turbo-preview   # Default model
EMBEDDING_MODEL=text-embedding-3-small  # Embedding model
```

#### Agent Configuration
```env
PARALLEL_EXECUTION=True    # Run agents in parallel
MAX_AGENT_RETRIES=3       # Retry attempts on failure
```

#### Security
```env
SECRET_KEY=your-secret-key-change-in-production  # JWT secret
ACCESS_TOKEN_EXPIRE_MINUTES=30                   # Token expiry
```

#### Logging
```env
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=console    # console or json
```

---

## 🏃 Running the Application

### Development Mode

```bash
# With auto-reload
python main.py
```

The API will start at: `http://localhost:8000`

### Production Mode

```bash
# Using Uvicorn with workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Future)

```bash
docker build -t rfp-backend .
docker run -p 8000:8000 --env-file .env rfp-backend
```

---

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Example API Calls

#### Scan for New RFPs
```bash
curl -X POST http://localhost:8000/api/rfp/scan
```

#### Get Latest RFPs
```bash
curl http://localhost:8000/api/rfp/latest?limit=10
```

#### Search Products
```bash
curl -X POST http://localhost:8000/api/products/search \
  -H "Content-Type: application/json" \
  -d '{"query": "11 kV XLPE Cable", "top_k": 5}'
```

#### Get Dashboard Analytics
```bash
curl http://localhost:8000/api/analytics/dashboard
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_agents.py
pytest tests/test_api.py
```

### Run with Verbose Output

```bash
pytest -v -s
```

---

## 📁 Project Structure

```
backend/
├── agents/                 # AI Agents
│   ├── base_agent.py       # Abstract base agent
│   ├── technical_agent.py  # Product matching agent
│   ├── pricing_agent.py    # Pricing calculation agent
│   └── orchestrator.py     # Agent coordinator
│
├── api/                    # API Layer
│   ├── routes/             # API endpoints
│   │   ├── health.py       # Health checks
│   │   ├── rfp.py          # RFP operations
│   │   ├── products.py     # Product operations
│   │   ├── analytics.py    # Analytics endpoints
│   │   └── agents.py       # Agent monitoring
│   └── schemas.py          # Pydantic models
│
├── config/                 # Configuration
│   └── settings.py         # App settings
│
├── data/                   # Data Layer
│   ├── product_loader.py   # Load CSV data
│   ├── vector_store.py     # ChromaDB wrapper
│   ├── product_matcher.py  # Matching logic
│   └── pricing_calculator.py
│
├── db/                     # Database
│   ├── database.py         # Connection & session
│   └── models.py           # SQLAlchemy models
│
├── services/               # Business Logic
│   ├── rfp_scanner.py      # Directory scanning
│   └── rfp_processor.py    # RFP processing
│
├── utils/                  # Utilities
│   ├── logger.py           # Logging setup
│   └── standards_checker.py # Compliance checker
│
├── tests/                  # Test Suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_agents.py      # Agent tests
│   └── test_api.py         # API tests
│
├── scripts/                # Utility Scripts
│   └── init_db.py          # Database initialization
│
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
└── .gitignore              # Git ignore rules
```

---

## 💻 Development

### Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Pre-commit Hooks (Recommended)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Dependencies

```bash
# Install package
pip install package-name

# Update requirements
pip freeze > requirements.txt
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Ensure you're in the correct directory
cd d:\Haki_FMCG\backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
```

#### 2. Database Connection Errors
```bash
# Check DATABASE_URL in .env
# For development, use SQLite:
DATABASE_URL=sqlite+aiosqlite:///./rfp_system.db
```

#### 3. Missing API Keys
```bash
# Verify .env file has:
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key
```

#### 4. Port Already in Use
```bash
# Change port in .env
API_PORT=8001

# Or kill process on port 8000
netstat -ano | findstr :8000  # Windows
kill -9 $(lsof -t -i:8000)    # Linux/Mac
```

#### 5. Package Installation Fails
```bash
# Try development requirements (no PostgreSQL)
pip install -r requirements-dev.txt

# Or install packages individually
pip install fastapi uvicorn sqlalchemy aiosqlite
```

### Getting Help

- Check logs: `tail -f logs/app.log`
- Enable debug mode: `DEBUG=True` in .env
- Test imports: `python -c "from config.settings import settings; print('OK')"`

---

## 📊 Performance

- **Request Latency**: < 200ms (cached)
- **Agent Processing**: 15-30s per RFP
- **Parallel Agents**: 2x faster than sequential
- **Database Queries**: Indexed for sub-second response

---

## 🔒 Security

- ✅ Environment-based secrets management
- ✅ CORS protection configured
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (ORM)
- ✅ Structured audit logging
- ⚠️ JWT authentication (coming soon)

---

## 🗺️ Roadmap

- [ ] JWT authentication & authorization
- [ ] Document generation (DOCX export)
- [ ] Email notifications
- [ ] Admin dashboard UI
- [ ] Multi-tenancy support
- [ ] Real-time WebSocket updates
- [ ] PDF text extraction improvements
- [ ] Additional agent types

---

## 📄 License

This project is proprietary and confidential.

---

## 👥 Contributors

- **Backend Development**: AI-Powered Multi-Agent Architecture
- **Data Integration**: Product catalogs and standards
- **Testing & QA**: Comprehensive test coverage

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Enable debug logging: `LOG_LEVEL=DEBUG`
4. Contact the development team

---

**Built with ❤️ using FastAPI, LangChain, and OpenAI**
