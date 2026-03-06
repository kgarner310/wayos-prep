# WAYOS PREP

**Retrieval-augmented meeting brief engine for commercial insurance producers.**

Ingests insurance-related sources, chunks and tags them, stores embeddings in Postgres with pgvector, retrieves relevant context for a producer query, and generates a structured pre-meeting brief.

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
- **Alembic migrations** (creates all 11 tables, HNSW vector index)
- **Seed script** (3 demo sources: roofing, trucking, manufacturing — parsed, chunked, tagged, marked ready)
- **FastAPI app** on port 8000 with hot reload

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"wayos-prep"}
```

### 4. Use It

Open **http://localhost:8000/admin/** in your browser.

**Full demo flow (no OpenAI key needed):**

1. Go to http://localhost:8000/admin/sources — see 3 seeded sources with status "ready"
2. Click a source — see tags, chunks, raw text
3. Go to http://localhost:8000/admin/prep
4. Enter: Industry `roofing`, State `NC`, Employees `22`
5. Click **Generate Brief**
6. Get back a structured brief with loss drivers, blind spots, questions, watchouts, citations
7. Click a feedback button (thumbs up/down, flag hallucination, etc.)
8. Go to http://localhost:8000/admin/briefs — click into the brief detail
9. See retrieval debug: which chunks were selected, similarity/rerank scores, filters used

**If you have an OpenAI key:**

Set `OPENAI_API_KEY` in `.env`, restart, then:
1. Click "Embed" on each source in the admin to generate vector embeddings
2. Queries now use vector similarity search + blended reranking
3. Brief generation uses GPT-4o-mini for richer, source-grounded output

### 5. API Docs

Interactive Swagger docs at http://localhost:8000/docs

### 6. Run Tests

```bash
# Unit tests — no database needed, run anywhere
pip install -r requirements.txt
pytest tests/test_chunker.py tests/test_parser.py tests/test_tagging.py tests/test_scoring.py tests/test_brief_schema.py -v

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
| LLM/Embeddings | OpenAI API (optional) |
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
| `POST` | `/api/v1/prep/query` | Submit query, get brief |
| `GET` | `/api/v1/prep/brief/{id}` | Get stored brief |
| `POST` | `/api/v1/feedback` | Submit feedback on a brief |
| `GET` | `/api/v1/retrieval/debug/{query_id}` | Retrieval debug info |

## Pipeline

```
Ingest → Parse/Clean → Chunk → Tag → Embed (optional) → Ready
                                                           ↓
Query → Normalize → Filter → Vector or Tag Search → Rerank → Brief Generation
                                                               ↓
                                                    JSON Brief + Markdown + Citations
```

### Retrieval Scoring

```
final_score = 0.45 * vector_similarity
            + 0.20 * tag_overlap
            + 0.15 * authority_score_normalized
            + 0.10 * freshness_score_normalized
            + 0.10 * jurisdiction_match
```

Without embeddings, vector_similarity is 0.0 and tag-based scoring drives ranking.
Both vector and tag-based search pre-filter by industry and jurisdiction tags.

## Project Structure

```
app/
  api/routes.py          # 12 REST API endpoints
  api/admin.py           # 6 admin UI pages (server-rendered HTML)
  core/config.py         # Settings from env vars
  core/enums.py          # Controlled values + starter tag lists
  db/session.py          # SQLAlchemy session (lazy engine init)
  models/models.py       # 11 tables (pgvector for embeddings)
  schemas/schemas.py     # Pydantic request/response validation
  services/
    ingestion.py         # Text, URL, file ingestion
    parser.py            # Text cleaning (nav/footer removal, whitespace normalization)
    chunker.py           # Heading-aware chunking (300-800 tokens, overlap)
    tagging.py           # Rule-based + optional LLM tag extraction
    embeddings.py        # OpenAI embedding generation
    retrieval.py         # Vector search + tag fallback + blended reranking
    brief_generator.py   # LLM brief generation + deterministic fallback
    scoring.py           # Authority + freshness scoring
  templates/             # Jinja2 HTML (6 pages)
  static/style.css       # Minimal admin CSS
  main.py                # FastAPI app entry point
alembic/                 # Database migrations
tests/                   # 32 unit tests
Dockerfile
docker-compose.yml
seed_data.py             # 3 demo sources (roofing, trucking, manufacturing)
```

## Assumptions

- OpenAI API key is optional. Without it: tag-based retrieval + deterministic briefs from chunk analysis
- pgvector HNSW index (works on empty tables, no training data needed)
- Chunks target 300-800 tokens with ~50-token overlap between adjacent chunks
- Demo sources cover roofing (NC), trucking (national), manufacturing (NC)
- Tagging is conservative — better to miss a tag than hallucinate one
