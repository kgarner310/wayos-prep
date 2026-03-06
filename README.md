# WAYOS PREP

**Retrieval-augmented meeting brief engine for commercial insurance producers.**

WAYOS PREP ingests insurance-related sources, chunks and tags them, stores embeddings in Postgres with pgvector, retrieves relevant context for a producer query, and generates a structured pre-meeting brief.

## Tech Stack

- **Backend:** Python + FastAPI + SQLAlchemy + Alembic
- **Database:** PostgreSQL + pgvector
- **LLM/Embeddings:** OpenAI API (GPT-4o-mini + text-embedding-3-small)
- **Frontend:** Server-rendered admin UI (Jinja2 templates)
- **Dev:** Docker Compose

## Quick Start

### 1. Configure

```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY for embeddings + LLM brief generation
# The app works without it (tag-based retrieval + fallback briefs) but is better with it
```

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- **PostgreSQL + pgvector** on port 5432
- **FastAPI app** on port 8000 (runs migrations, seeds demo data, starts uvicorn with reload)

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"wayos-prep"}

# Open admin UI:
open http://localhost:8000/admin/
```

### 4. Demo Flow

The seed script auto-creates 3 sample sources (roofing, trucking, manufacturing) with chunks and tags.

1. **View sources** at http://localhost:8000/admin/sources
2. **Click a source** to see details, tags, chunks
3. **If you have an OpenAI key:** click "Embed" on each source to generate embeddings
4. **Run a prep query** at http://localhost:8000/admin/prep
   - Industry: `roofing`, State: `NC`, Employees: `22`
   - Click "Generate Brief"
5. **View the brief** with markdown + JSON output
6. **Submit feedback** (thumbs up/down, flag hallucination, etc.)
7. **Inspect retrieval debug** at http://localhost:8000/admin/briefs/{brief_id}

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/sources/ingest` | Ingest source from raw text |
| POST | `/api/v1/sources/ingest/url` | Ingest source from URL |
| POST | `/api/v1/sources/ingest/file` | Ingest source from file upload |
| POST | `/api/v1/sources/{id}/parse` | Parse, clean, and tag source |
| POST | `/api/v1/sources/{id}/chunk` | Chunk source text |
| POST | `/api/v1/sources/{id}/embed` | Generate embeddings for chunks |
| GET | `/api/v1/sources` | List all sources |
| GET | `/api/v1/sources/{id}` | Source detail with tags and chunks |
| POST | `/api/v1/prep/query` | Submit prep query, get brief |
| GET | `/api/v1/prep/brief/{id}` | Get stored brief |
| POST | `/api/v1/feedback` | Submit feedback on a brief |
| GET | `/api/v1/retrieval/debug/{query_id}` | Retrieval debug info |

Interactive API docs at http://localhost:8000/docs

## Admin UI

- **Dashboard** — `/admin/` — stats, quick actions, source ingestion form
- **Sources** — `/admin/sources` — list all sources with status
- **Source Detail** — `/admin/sources/{id}` — tags, chunks, parse/chunk/embed buttons
- **Run Prep** — `/admin/prep` — query form with brief output + feedback
- **Briefs** — `/admin/briefs` — list generated briefs
- **Brief Detail** — `/admin/briefs/{id}` — brief output, retrieval debug, feedback

## Pipeline

```
Source Ingestion → Parse/Clean → Chunk → Tag → Embed → Ready
                                                         ↓
Query → Normalize → Filter → Vector Search → Rerank → Brief Generation
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

## Project Structure

```
/wayos-prep
  /app
    /api            # FastAPI routes (API + admin UI)
    /core           # Config, enums, constants
    /db             # Database session
    /models         # SQLAlchemy models (pgvector)
    /schemas        # Pydantic request/response schemas
    /services       # Business logic
      ingestion.py    # Source ingestion (text, URL, file)
      parser.py       # Text cleaning
      chunker.py      # Heading-aware chunking
      tagging.py      # Rule-based + LLM tag extraction
      embeddings.py   # OpenAI embedding generation
      retrieval.py    # Vector search + reranking
      brief_generator.py  # LLM brief generation
      scoring.py      # Authority + freshness scoring
    /templates      # Jinja2 HTML templates
    /static         # CSS
    main.py         # FastAPI app
  /alembic          # Database migrations
  /tests            # pytest tests
  /docker           # Dockerfile
  docker-compose.yml
  seed_data.py      # Demo data seeder
  requirements.txt
  .env.example
```

## Running Tests

```bash
# Unit tests (no database needed)
pytest tests/test_chunker.py tests/test_parser.py tests/test_tagging.py tests/test_scoring.py tests/test_brief_schema.py -v

# API tests (requires test database)
TEST_DATABASE_URL=postgresql://wayos:wayos_dev_password@localhost:5432/wayos_prep_test pytest tests/test_api.py -v
```

## Assumptions

- OpenAI API key is optional but recommended for full functionality (embeddings + LLM briefs)
- Without an API key, the system uses tag-based retrieval and fallback brief generation
- pgvector IVFFlat index uses 100 lists (appropriate for <100K vectors)
- Chunks target 300-800 tokens with light overlap
- Demo sources cover roofing, trucking, and manufacturing in NC

## Next Steps

- Add more seed sources across all starter industries
- Implement PDF upload parsing
- Add batch processing endpoint for ingestion pipeline
- Build source freshness decay job
- Add user auth when needed
- Implement proper reranker (cross-encoder)
- Add brief template customization
- Build export (PDF/email) for briefs
