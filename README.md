# WAYOS PREP

**Better meetings. Better coverage.**

WAYOS PREP is a meeting preparation engine for commercial insurance producers. It generates structured client risk briefs for any industry, helping producers walk into every meeting prepared.

## Tech Stack

- **Frontend:** React Native + Expo (Expo Go compatible) + Expo Router
- **Backend:** Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- **Database:** PostgreSQL
- **LLM:** OpenAI / Anthropic / None (deterministic mode)

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env if you want to use an LLM provider (optional)
```

### 2. Start backend with Docker

```bash
cd infra
docker compose up --build
```

This starts PostgreSQL and the FastAPI backend. On first run, it will:
- Run database migrations
- Seed 20 industry risk profiles

The API is available at `http://localhost:8000`.

### 3. Verify the backend

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"wayos-prep"}

curl http://localhost:8000/industries
# Returns list of 20 industries
```

### 4. Start the mobile app

```bash
cd frontend
npm install
npx expo start
```

Scan the QR code with Expo Go on your phone. Make sure your phone can reach the backend (you may need to set `EXPO_PUBLIC_API_BASE_URL` to your machine's LAN IP).

```bash
# Example: set API URL to your machine's IP
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000 npx expo start
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/industries` | List all industries |
| GET | `/industries/{id}` | Get industry detail |
| POST | `/briefs/ask` | Generate brief from a question |
| POST | `/briefs/prep` | Generate brief from account details |
| GET | `/briefs/{id}` | Retrieve a generated brief |
| POST | `/feedback` | Submit brief feedback |

## Core Features

### 1. Ask Risk Question
Ask a natural language question like "What risks should I discuss with a roofing contractor?" and get a full client brief.

### 2. Prep This Account
Enter industry, location, employee count, MOD, and vehicle exposure to generate a tailored brief.

### 3. Industry Lookup
Browse and search 20 seeded industries. View risk profiles and generate briefs.

### Brief Output
Each brief includes:
- **Top Claim Drivers** — what actually hurts in this industry
- **Regional Risk Notes** — location-specific considerations
- **Coverage Exposures** — what to stress-test
- **Conversation Starters** — questions producers can ask
- **Quick Docs to Request** — standard document checklist

### Send Pack (Viral Sharing)
From any brief, share pre-formatted messages:
- **Underwriter Email** — professional email to underwriters
- **Internal Note** — CSR/team account prep summary

## LLM Configuration

Set `LLM_PROVIDER` in `.env`:

| Value | Behavior |
|-------|----------|
| `none` | Deterministic briefs from seed data (default, no API key needed) |
| `openai` | Uses GPT-4o-mini for industry matching and regional notes |
| `anthropic` | Uses Claude Haiku for industry matching and regional notes |

The system works fully without any LLM — the seed data provides complete risk profiles.

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
/wayos-prep
  /backend
    /app
      /models        # SQLAlchemy models
      /services      # Business logic
      /api           # FastAPI routes
    /tests           # pytest tests
    /alembic         # Database migrations
  /frontend
    /app             # Expo Router screens
    /components      # Shared UI components
    /services        # API client and theme
  /infra
    docker-compose.yml
  /docs
    demo.md
```
