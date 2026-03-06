# WAYOS PREP

**Standalone meeting-prep and account-review app for commercial insurance producers.**

WAYOS PREP helps producers prepare for meetings, discover risk, find coverage gaps, and build sharper underwriting submissions — all from a single web interface. Ingest insurance-related sources, run a prep query, and get back a structured brief with loss drivers, coverage gap detection, producer ammo, and actionable questions.

## What It Does

- **Pre-Meeting Briefs** — Structured loss drivers, coverage blind spots, and questions-to-ask with source citations
- **Coverage Gap Detector** — Deterministic gap analysis based on industry, state, mod, fleet exposure, and account traits
- **Producer Ammo** — Sharp, meeting-ready talking points: renewal leverage, underwriting hot buttons, cross-sell openings, and hard questions
- **Risk Scoring** — 6-layer deterministic risk scoring with explainable components and risk band assignment
- **Risk Theme Graph** — Industry/department-aware graph expansion for intelligent risk discovery
- **Source Intelligence** — Ingests, chunks, tags, and embeds insurance documents for retrieval-augmented analysis

## Quick Start

### 1. Configure

```bash
cp .env.example .env
# Optional: add your OPENAI_API_KEY for embeddings + LLM brief generation
# The app works without it — tag-based retrieval + deterministic briefs
```

### 2. Start

```bash
docker compose up --build
```

This runs:
- **PostgreSQL 16 + pgvector** on port 5432
- **Alembic migrations** (creates all tables, HNSW vector index)
- **Seed script** (demo sources: roofing, trucking, manufacturing — parsed, chunked, tagged, ready)
- **FastAPI app** on port 8000 with hot reload

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"wayos-prep"}
```

### 4. Use It

Open **http://localhost:8000/admin/** in your browser.

**Full demo flow (no OpenAI key needed):**

1. Go to http://localhost:8000/admin/prep
2. Enter: Industry `roofing`, State `NC`, Employees `22`, Mod `1.15`
3. Click **Generate Brief**
4. Get back a structured brief with:
   - Top loss drivers with confidence levels
   - Coverage blind spots
   - Questions to ask
   - **Coverage Gap Detector** — specific gaps with severity, reasoning, and suggested actions
   - **Producer Ammo** — renewal pressure points, underwriting hot buttons, cross-sell openings, hard questions
5. Switch tabs: Markdown | Coverage Gaps | Producer Ammo | JSON
6. Click a feedback button (thumbs up/down, flag hallucination, etc.)
7. Go to http://localhost:8000/admin/briefs — click into the brief detail for full retrieval debug

**If you have an OpenAI key:**

Set `OPENAI_API_KEY` in `.env`, restart, then:
1. Click "Embed" on each source in the admin to generate vector embeddings
2. Queries now use vector similarity search + blended reranking
3. Brief generation uses GPT-4o-mini for richer, source-grounded output

### 5. API Docs

Interactive Swagger docs at http://localhost:8000/docs

### 6. Run Tests

```bash
# Unit tests — no database needed
pip install -r requirements.txt
pytest tests/ -v -k "not test_api"

# API tests — requires a running Postgres with pgvector
DATABASE_URL=postgresql://wayos:wayos_dev_password@localhost:5432/wayos_prep pytest tests/test_api.py -v
```

### 7. Tear Down

```bash
docker compose down        # stop containers
docker compose down -v     # stop + delete database volume
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 + pgvector (HNSW index) |
| LLM/Embeddings | OpenAI API (optional — works without it) |
| Admin UI | Jinja2 templates + vanilla CSS |
| Dev | Docker Compose |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/sources/ingest` | Ingest source from raw text |
| `POST` | `/api/v1/sources/ingest/url` | Ingest source from URL |
| `POST` | `/api/v1/sources/ingest/file` | Ingest source from file upload |
| `POST` | `/api/v1/sources/{id}/parse` | Parse, clean, and tag source |
| `POST` | `/api/v1/sources/{id}/chunk` | Chunk source text |
| `POST` | `/api/v1/sources/{id}/embed` | Generate embeddings (requires OpenAI key) |
| `GET` | `/api/v1/sources` | List sources |
| `GET` | `/api/v1/sources/{id}` | Source detail with tags and chunks |
| `POST` | `/api/v1/prep/query` | Submit query, get brief + risk score |
| `GET` | `/api/v1/prep/brief/{id}` | Get stored brief |
| `POST` | `/api/v1/feedback` | Submit feedback on a brief |
| `GET` | `/api/v1/retrieval/debug/{query_id}` | Retrieval debug info |
| `POST` | `/api/v1/risk-score` | Run standalone risk scoring |
| `GET` | `/api/v1/risk-score/{query_id}` | Get risk score for a query |

## Pipeline

```
Ingest → Parse/Clean → Chunk → Tag → Embed (optional) → Ready
                                                           ↓
Query → Normalize → Filter → Vector or Tag Search → Rerank → Brief Generation
                                                               ↓
                                              JSON Brief + Coverage Gaps + Producer Ammo
                                                               ↓
                                                    Risk Scoring (6-layer deterministic)
```

## Brief Output Structure

Each brief includes:
- **Top Loss Drivers** — risk themes with confidence and source attribution
- **Coverage Blind Spots** — missing or under-covered lines
- **Questions to Ask** — producer questions with purpose
- **Watchouts** — operational warnings
- **Coverage Gap Detector** — deterministic gap analysis with severity, reasoning, suggested questions, and actions
- **Producer Ammo** — renewal pressure points, underwriting hot buttons, cross-sell openings, hard questions
- **Confidence Notes** — source quality and coverage warnings
- **Citation Map** — source attribution

## Project Structure

```
app/
  api/routes.py              # REST API endpoints
  api/admin.py               # Admin UI pages (server-rendered HTML)
  core/config.py             # Settings from env vars
  core/enums.py              # Controlled values + starter tag lists
  db/session.py              # SQLAlchemy session
  models/models.py           # Database tables (pgvector for embeddings)
  schemas/schemas.py         # Pydantic request/response validation
  services/
    ingestion.py             # Text, URL, file ingestion
    parser.py                # Text cleaning
    chunker.py               # Heading-aware chunking
    tagging.py               # Rule-based + optional LLM tag extraction
    embeddings.py            # OpenAI embedding generation
    retrieval.py             # Vector search + tag fallback + blended reranking
    brief_generator.py       # LLM brief generation + deterministic fallback
    coverage_gap_detector.py # Deterministic coverage gap analysis
    producer_ammo.py         # Producer meeting ammo generation
    risk_scoring.py          # 6-layer account risk scoring
    graph_expansion.py       # Risk theme graph traversal
    producer_questions.py    # DB-backed producer question library
    scoring.py               # Authority + freshness scoring
  templates/                 # Jinja2 HTML pages
  static/style.css           # Admin CSS
  main.py                    # FastAPI app entry point
alembic/                     # Database migrations
tests/                       # Unit tests
seed_data.py                 # Demo sources (roofing, trucking, manufacturing)
seed_graph.py                # Risk theme graph + producer question seeding
```
