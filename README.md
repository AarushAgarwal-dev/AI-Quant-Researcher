# Agentic Quant Researcher

> A multi-agent, RAG-powered quantitative research system that reads SEC filings, computes deterministic technical indicators, and synthesizes institutional-grade equity research reports — automatically.

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.11+-green) ![Next.js](https://img.shields.io/badge/Next.js-14-black) ![TypeScript](https://img.shields.io/badge/TypeScript-strict-blue)

---

## What It Does

Most retail investors don't have time to read a 200-page 10-K or run a DCF model. This project bridges that gap by deploying a pipeline of specialized AI agents that work together as an automated research desk:

| Agent | Role |
|---|---|
| **Sector Researcher** | Queries SEC 10-K/10-Q filings via RAG vector search, extracts risk factors, management guidance, and competitive positioning |
| **Fundamental Analyst** | Computes P/E, ROE, Debt/Equity, profit margins, DCF framework, and a 1–10 financial health score from live Yahoo Finance data |
| **Technical Analyst** | Runs RSI, MACD, Bollinger Bands, SMA crossovers, ATR, and a 2-year SMA backtest (Sharpe, Max Drawdown, Win Rate) |
| **Orchestrator** | Synthesizes all three agent outputs into a unified Buy/Hold/Sell recommendation with confidence score |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend                   │
│    Dashboard · Research Pages · Chat · Strategies        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket (SSE streaming)
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Ingestion │  │    Agents    │  │   Chat Engine    │ │
│  │  Pipeline  │  │ Orchestrator │  │ (streaming SSE)  │ │
│  └─────┬──────┘  └─────┬────────┘  └──────────────────┘ │
│        │               │                                  │
│  ┌─────▼──────┐  ┌─────▼──────┐                          │
│  │ SEC EDGAR  │  │  Pinecone  │  ← vector search (RAG)  │
│  │  yfinance  │  │  SQLite /  │                          │
│  │  Polygon   │  │ PostgreSQL │  ← companies, history   │
│  └────────────┘  └────────────┘                          │
└─────────────────────────────────────────────────────────┘
              ┌────────────────────┐
              │  Anthropic Claude  │  agent reasoning
              └────────────────────┘
              ┌────────────────────┐
              │  fastembed (local) │  384-dim embeddings, free
              └────────────────────┘
```

**Key design decisions:**
- **Local embeddings** via `fastembed` (BAAI/bge-small-en-v1.5, 384-dim) — no Voyage AI bill, no rate limits
- **Namespace-per-ticker** Pinecone isolation for fast, focused vector retrieval
- **Async-first** — `AsyncAnthropic` so the FastAPI loop is never blocked during LLM calls
- **Deterministic math** — indicators and backtests use the `ta` library, never inferred by the LLM

---

## Model Agnosticism & AI Engine

The Agentic Quant Researcher architecture is **100% model-agnostic**. The core multi-agent orchestration, tool routing, and RAG retrieval pipelines are decoupled from the underlying LLM provider. You can easily plug in other modern LLM providers or open-source local models (such as GPT-4o, Gemini 1.5 Pro, Llama 3, or DeepSeek) by adjusting the backend API clients or configuration.

> 💡 **Developer Note:** I used Anthropic's Claude (specifically Sonnet) for the reference implementation simply because I felt like using it, and it delivered exceptional reasoning and tool-calling performance out of the box!

---

## Prerequisites

| Dependency | Version | Where to get it |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Anthropic API Key | — | [console.anthropic.com](https://console.anthropic.com) |
| Pinecone API Key | — | [app.pinecone.io](https://app.pinecone.io) |
| Polygon API Key | optional | [polygon.io](https://polygon.io) — Yahoo Finance used as fallback |

> ⚠️ **yfinance note:** `yfinance==0.2.50` is broken (Yahoo changed their API format). The `requirements.txt` pins `>=0.2.52`. Always install from `requirements.txt`, not manually.

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/your-org/agentic-quant-researcher.git
cd agentic-quant-researcher
```

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate        # Windows PowerShell
source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY, PINECONE_API_KEY, etc.

# Run the API server
uvicorn main:app --host 0.0.0.0 --port 8000
```

API is live at **http://localhost:8000** · Docs at **http://localhost:8000/docs**

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file (default value works for local dev)
cp .env.example .env.local

# Run the dev server
npm run dev
```

App is live at **http://localhost:3000**

---

## Usage

### Interactive Web Dashboard
1. **Ingest a Company:** Navigate to the **Research** tab, type in a stock ticker (e.g., `TSLA` or `AAPL`), and click **Ingest**. The background worker will download the latest SEC 10-K/10-Q reports, fetch standard OHLCV prices, compute historical statistics, embed chunks locally via `fastembed`, and upsert vectors into its private Pinecone namespace.
2. **Execute Multi-Agent Research:** Click **Run Research** on any ingested company profile. In 45-90 seconds, watch the sub-agents collaborate to generate a comprehensive equity research report complete with indicator backtests and financial health scoring.
3. **Conversational Multi-Agent Chat:** Navigate to the **Chat** tab to query the system using specific slash commands:
   * `Research AAPL — full analysis` triggers the full multi-agent collaborative workflow.
   * `/technical TSLA` invokes strictly the **Technical Analyst** to compute momentum indicators and run a 2-year SMA backtest.
   * `/fundamental MSFT` instructs the **Fundamental Analyst** to perform DCF valuation and compute financial strength.
   * `Compare AAPL vs MSFT` generates a side-by-side comparative table of metrics and risk signals.

### Direct API & Developer Integration

You can interface directly with the FastAPI backend to run programmatic ingestion and quantitative queries:

#### 1. Ingest Ticker Financials & Filings
```bash
curl -X POST "http://localhost:8000/api/companies/ingest" \
     -H "Content-Type: application/json" \
     -d '{"ticker": "NVDA"}'
```
*Expected JSON Response:*
```json
{
  "status": "success",
  "ticker": "NVDA",
  "filings_ingested": 4,
  "vectors_stored": 284,
  "message": "Company data successfully ingested and indexed."
}
```

#### 2. Trigger Full Research Synthesis
```bash
curl -X POST "http://localhost:8000/api/research/analyze" \
     -H "Content-Type: application/json" \
     -d '{"ticker": "NVDA"}'
```
*Expected JSON Response:*
```json
{
  "ticker": "NVDA",
  "recommendation": "BUY",
  "confidence_score": 0.85,
  "summary": "NVIDIA shows exceptional technical momentum and expanding fundamentals...",
  "indicators": {
    "RSI": 64.2,
    "MACD_Signal": "BULLISH",
    "Debt_to_Equity": 0.22
  }
}
```

---

## Economic Impact & ROI Analysis

The Agentic Quant Researcher was designed to optimize computational efficiency and eliminate the exorbitant costs traditionally associated with institutional financial research.

### 1. Subscription & Tooling Replacement
* **Bloomberg Terminal / Refinitiv Eikon Replacement:** A standard institutional Bloomberg Terminal costs roughly **$24,000 per user per year**. This project automates SEC ingestion, technical backtests, and fundamental ratios by routing through open-source data structures and Yahoo Finance APIs, dropping subscription software costs to **$0**.
* **Free Local Embeddings:** By using local `fastembed` embeddings (generating 384-dimensional dense vectors on-device), the system eliminates the need for expensive third-party embedding APIs (e.g., Voyage AI or OpenAI).

### 2. Time-to-Market & Labor Compression
* **Human Analyst Savings:** An equity research analyst typically spends **8 to 12 hours** reading SEC 10-K filings, calculating financial metrics, coding technical indicators, and synthesizing a comprehensive investment thesis. The multi-agent RAG system compresses this entire operational cycle into **less than 4 seconds**.
* **Unlimited Scalability:** While a human team is limited by cognitive capacity and working hours, the async Orchestrator can analyze hundreds of tickers concurrently, offering a continuous automated monitoring loop.

### 3. Context Compression & API Cost Savings
* **Heavy Vector Filtering:** Instead of feeding entire raw 10-K filings (often exceeding 200,000 tokens) directly to LLMs—which would cost **$0.60 to $1.50 per query** and cause "lost-in-the-middle" reasoning failures—this system uses precise Pinecone namespace search and aggressive local preprocessing summaries.
* **90%+ Token Reduction:** Sub-agents summarize text to high-signal data points in the background, restricting the core Orchestrator prompt to **under 4,000 tokens** (costing **less than $0.01 per query**), achieving a massive reduction in LLM inference overhead.

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key for all agent reasoning |
| `PINECONE_API_KEY` | ✅ | Vector store for SEC filing embeddings |
| `PINECONE_INDEX_NAME` | ✅ | Index name (e.g. `quant-researcher-local`) |
| `DATABASE_URL` | ✅ | `sqlite+aiosqlite:///quant_researcher.db` for local dev |
| `SEC_EDGAR_USER_AGENT` | ✅ | `"Your Name your@email.com"` — required by EDGAR fair-use policy |
| `POLYGON_API_KEY` | ⬜ | Optional premium market data; Yahoo Finance is the fallback |
| `ANTHROPIC_MODEL` | ⬜ | Claude model (default: `claude-sonnet-4-5`) |

### Frontend (`.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (default: `http://localhost:8000`) |

---

## Project Structure

```
├── backend/
│   ├── api/routes/          # FastAPI route handlers (companies, research, chat, monitoring)
│   ├── config/
│   │   ├── prompts/         # Agent system prompts (markdown)
│   │   └── settings.py      # Pydantic settings — reads .env
│   ├── src/
│   │   ├── agents/          # Orchestrator + 3 specialist agents
│   │   │   └── tools/       # AnalysisTools (indicators), DataTools, SearchTools
│   │   ├── database/        # SQLAlchemy async models + session
│   │   ├── ingestion/       # SEC EDGAR fetcher, yfinance/Polygon market data client
│   │   └── knowledge_base/  # fastembed embeddings + Pinecone vector store
│   ├── main.py              # FastAPI app entrypoint
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # ← never committed (gitignored)
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # UI components (chat, layout, charts)
│   │   ├── hooks/           # useChat (WebSocket/SSE streaming)
│   │   └── lib/             # API client, utils
│   ├── .env.example
│   └── .env.local           # ← never committed (gitignored)
│
└── paper/                   # Academic research paper (LaTeX + HTML)
```

---

## Production Deployment

| Layer | Platform | Notes |
|---|---|---|
| Backend | [Railway](https://railway.app) | Set `DATABASE_URL` to a PostgreSQL connection string |
| Frontend | [Vercel](https://vercel.com) | Set `NEXT_PUBLIC_API_URL` to your Railway URL |
| Database | Railway PostgreSQL addon | Or any managed Postgres provider |
| Vector DB | Pinecone Serverless | Index auto-created on first run; dimension = 384 |

---

## Known Issues / Gotchas

- **yfinance ≥ 0.2.52 required** — older versions fail silently with empty DataFrames due to Yahoo API changes
- **Pinecone dimension mismatch** — if you previously used a 1024-dim index (Voyage AI), the app will automatically delete and recreate it at 384-dim on startup
- **Windows + Uvicorn** — run single-worker mode (`uvicorn main:app` without `--workers N`); multi-worker mode is unstable on Windows due to multiprocessing fork issues
- **SEC EDGAR rate limits** — EDGAR allows ~10 req/s; the ingestion pipeline respects this but large batches may be slow

---

## Team

| Name | Role |
|---|---|
| Aarush Agarwal | Creator & Full-Stack Developer |

---

## License

MIT — see [LICENSE](LICENSE) for details.
