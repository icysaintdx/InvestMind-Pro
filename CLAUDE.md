# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InvestMind Pro (智投顾问团) is a multi-agent AI-powered stock investment analysis system for the Chinese A-share market. It uses 21 specialized AI agents organized in 4 stages to provide collaborative investment analysis.

## Build and Run Commands

### Backend (Python/FastAPI)
```bash
pip install -r backend/requirements.txt
python backend/server.py
# Server: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend (Vue 3)
```bash
cd frontend
npm install
npm run serve    # Dev server at http://localhost:8080
npm run build    # Production build
npm run lint     # ESLint
```

### Quick Start (Windows)
```bash
start.bat
```

## Architecture

### Multi-Agent System (4 Stages)
- **Stage 1 - Analysts (5)**: Macro, Industry, Technical, Funds, Fundamental
- **Stage 2 - Managers (2)**: Fundamental Research Director, Market Momentum Director
- **Stage 3 - Risk Control (2)**: Systemic Risk Director, Portfolio Risk Director
- **Stage 4 - Decision (1)**: Investment Decision General Manager

### Key Directories
- `backend/` - FastAPI server
  - `api/` - Route handlers (30+ files)
  - `agents/` - AI agent definitions (analysts/, managers/, researchers/, risk_mgmt/, trader/)
  - `dataflows/` - Data source management and providers
  - `services/` - Business logic (llm/, strategy/, cache/)
  - `strategies/` - 20+ trading strategies
  - `backtest/` - Backtesting engine
- `frontend/` - Vue 3 frontend
  - `src/views/` - Page components
  - `src/components/` - Reusable components

### Data Flow Architecture
- **Primary data source**: AKShare (free, comprehensive)
- **Secondary**: Tushare, Juhe API
- **Fallback**: Local cache, default responses
- **Tiered caching**: L1 (memory, 5min) → L2 (Redis, 1hr) → L3 (file, 24hr)

### LLM Graceful Degradation
5-level fallback for LLM failures: Original → 50% compression → 25% compression → 10% minimal → Default response

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `GEMINI_API_KEY` - Google Gemini AI
- `DEEPSEEK_API_KEY` - DeepSeek AI
- `QWEN_API_KEY` - Alibaba Qwen AI
- `SILICONFLOW_API_KEY` - SiliconFlow platform
- `JUHE_API_KEY` - Juhe stock data
- `TUSHARE_TOKEN` - Tushare A-share data (optional)

## Key Files

| File | Purpose |
|------|---------|
| `backend/server.py` | Main FastAPI application entry point |
| `backend/agent_configs.json` | Agent model and temperature configuration |
| `backend/dataflows/interface.py` | Unified data access interface |
| `backend/dataflows/data_source_manager.py` | Multi-source data management |
| `frontend/src/App.vue` | Main Vue application |

## API Endpoints

- `POST /api/analyze` - Start stock analysis
- `GET /api/agents` - List all agents
- `GET /api/agent-config/*` - Agent configuration
- `GET /api/dataflow/*` - Data flow monitoring
- `POST /api/backtest/*` - Backtesting operations

## Notes

- Primary language is Chinese (comments, docs, UI)
- Database: SQLite (`InvestMindPro.db`, `backend/investmind.db`)
- Real-time updates via Server-Sent Events (SSE)
- `tradingagents/` is a compatibility layer for legacy imports
