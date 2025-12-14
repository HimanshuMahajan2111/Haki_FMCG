# Haki FMCG - RFP Response Automation System

Complete B2B RFP Response Automation with AI Multi-Agent System

## Project Structure

```
Haki_FMCG/
├── backend/              # FastAPI backend with AI agents
├── Frontend/             # React frontend application
├── FMEG_data/           # Product data (2,500+ items)
├── wires_cables_data/   # Wires & cables data (600+ items)
├── wires_cables_standards/  # Industry standards
├── testing_data/        # Testing procedures
└── RFPs/                # RFP documents (PDFs)
```

## Quick Start

### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # Configure API keys
python main.py            # Start at http://localhost:8000
```

### Frontend (React)
```bash
cd Frontend/tech
npm install
npm run dev              # Start at http://localhost:5173
```

## Documentation

- [Backend README](backend/README.md) - Complete backend setup and API docs
- [Frontend README](Frontend/tech/README.md) - React app documentation

## Features

- ✅ AI-powered RFP analysis using GPT-4
- ✅ Semantic product matching with vector search
- ✅ Automatic standards compliance checking
- ✅ Intelligent pricing with volume discounts
- ✅ Multi-agent parallel processing
- ✅ Real-time analytics dashboard

## License

Proprietary and Confidential
