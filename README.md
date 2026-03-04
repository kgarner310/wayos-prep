# WAYOS PREP

**Better meetings. Better coverage.**

WAYOS PREP is a meeting preparation engine for commercial insurance producers, delivered as an **Outlook Add-in**. It generates structured client risk briefs for any industry — right inside the tool producers already use all day.

## Tech Stack

- **Frontend:** Outlook Add-in (Office.js + React + Vite)
- **Backend:** Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- **Database:** PostgreSQL
- **LLM:** OpenAI / Anthropic / None (deterministic mode)

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env if you want to use an LLM provider (optional)
```

### 2. Start everything with Docker

```bash
cd infra
docker compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **FastAPI backend** on port 8000 (runs migrations + seeds 20 industries)
- **Vite dev server** on port 3000 (serves the Outlook Add-in)

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"wayos-prep","database":"connected"}

# Open the task pane standalone in a browser:
open http://localhost:3000
```

### 4. Sideload into Outlook

**For Outlook on the web (easiest for testing):**

1. Open Outlook at https://outlook.office.com
2. Click the **Get Add-ins** button (or **Manage Add-ins** from the ... menu)
3. Click **My add-ins** → **Add a custom add-in** → **Add from file**
4. Upload `frontend/public/manifest.xml`
5. The **WAYOS PREP** button appears in the ribbon

**For Outlook desktop:**

1. Open Outlook → File → Manage Add-ins
2. Under **Custom add-ins**, click **Add from file**
3. Select `frontend/public/manifest.xml`

**Note:** For production, update the URLs in `manifest.xml` from `https://localhost:3000` to your deployed domain.

### 5. Standalone browser mode

The add-in also works as a standalone web app at `http://localhost:3000`. Outside Outlook, the Send Pack buttons copy to clipboard instead of opening compose windows.

## How It Works in Outlook

1. **Open a calendar invite** for a client meeting → Click **WAYOS PREP** in the ribbon
2. The add-in reads the appointment subject and suggests the industry
3. **Generate a brief** with one click
4. **Send Pack** opens a new email compose window pre-filled with the underwriter email or CSR note
5. The producer never leaves Outlook

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (includes DB status) |
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

### Send Pack (Outlook-Native Sharing)
From any brief, launch pre-formatted messages:
- **Underwriter Email** — opens Outlook compose with subject line and body pre-filled
- **Internal Note** — opens compose with CSR-ready account prep summary

When running outside Outlook (standalone browser), Send Pack copies to clipboard instead.

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
DATABASE_URL=sqlite:///test.db pytest tests/ -v
```

## Project Structure

```
/wayos-prep
  /backend
    /app
      /models        # SQLAlchemy models
      /services      # Business logic (matching, brief rendering, LLM)
      /api           # FastAPI routes
    /tests           # pytest tests
    /alembic         # Database migrations
  /frontend
    /public          # manifest.xml (Office Add-in), taskpane.html
    /src
      /components    # Button, Card, Input, Section
      /screens       # Home, Ask, Prep, Lookup, IndustryDetail, Brief
      /services      # API client, Office.js helpers, theme
  /infra
    docker-compose.yml
  /docs
    demo.md
```

## Manifest Configuration

The add-in manifest (`frontend/public/manifest.xml`) registers WAYOS PREP for:

- **Message Read** — prep while reading client emails
- **Message Compose** — insert brief content into emails
- **Appointment Organizer** — prep before meetings you scheduled
- **Appointment Attendee** — prep before meetings you're invited to

Update `<SourceLocation>` URLs for production deployment.
