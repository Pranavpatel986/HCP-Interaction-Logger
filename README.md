# AI-First CRM — HCP Module: Log Interaction Screen

An AI-first CRM module for pharma/life-science field representatives to log
their interactions with Healthcare Professionals (HCPs), either through a
**structured form** or a **conversational chat interface** powered by a
**LangGraph agent** running on **Groq (gemma2-9b-it)**.

## Architecture

```
frontend/  React + Redux Toolkit (Vite)
backend/   FastAPI + SQLAlchemy + LangGraph + Groq
database/  PostgreSQL (or MySQL — swap the SQLAlchemy URL)
```

- The **structured form** posts directly to `POST /interactions`.
- The **chat interface** posts to `POST /chat`, which runs a LangGraph agent.
  The agent decides which of the 5 tools to call based on the rep's message,
  then replies conversationally and the frontend refreshes the interaction
  list.

## Why LangGraph here

The LangGraph agent is the orchestration layer between the rep's natural
language and the CRM's structured data model. It:

1. Maintains conversational state across turns (so a rep can say "log this
   visit" and then later "actually change the sentiment to positive"
   without repeating context).
2. Routes each message to the right **tool** (a Python function with a
   clear, single responsibility) rather than trying to do everything in one
   giant prompt.
3. Lets tools call the LLM internally for sub-tasks (e.g. `log_interaction`
   uses the LLM purely for entity extraction/summarization, not for
   deciding what to do next — that routing decision stays with the graph).

This mirrors how a real rep would work: describe what happened in plain
language, and let the system figure out what needs to be logged, edited, or
scheduled.

## The 5 LangGraph Tools

| Tool | Purpose |
|---|---|
| `log_interaction` (required) | Takes the rep's free-text note, uses the LLM to extract interaction type, products discussed, samples given, HCP sentiment, and follow-up needs, then writes a structured `Interaction` row. |
| `edit_interaction` (required) | Takes an interaction ID + a natural-language change request (e.g. "push the follow-up to next Friday"), uses the LLM to compute a diff, and applies it. |
| `search_hcp_profile` | Looks up an HCP by name/ID and returns their profile + last 5 interactions, so the agent has context before logging or editing. |
| `schedule_follow_up` | Creates a `FollowUpTask` tied to an interaction with a due date and description. |
| `generate_call_prep_summary` | Summarizes an HCP's recent interaction history into a short call-prep brief for the rep's next visit. |

See `backend/app/agent/tools.py` for implementations and
`backend/app/agent/graph.py` for how they're wired into the LangGraph
`StateGraph` (a standard agent → tools → agent loop using
`langgraph.prebuilt.ToolNode` and `tools_condition`).

## Data Model

- `hcps` — HCP profile (name, specialty, territory, hospital)
- `interactions` — logged interactions, tagged `source = "form" | "chat"`
- `follow_up_tasks` — follow-up tasks created by the agent or the form

## Running it locally

### 1. Database
Create a Postgres database (or MySQL, adjusting the connection string):
```bash
createdb hcp_crm
```

### 2. Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GROQ_API_KEY
python seed.py          # creates tables + a few demo HCPs
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 — the Vite dev server proxies `/api` to the
FastAPI backend on port 8000.

### 4. Try it
- **Structured Form tab**: pick a seeded HCP, fill in the fields, save.
- **Chat tab**: type something like *"I met Dr. Sarah Chen today, discussed
  Drug A, she seemed positive and wants follow-up trial data next week"* —
  the agent will search for the HCP, log the interaction, and confirm back.
  Then try *"actually change that sentiment to Neutral"* to see
  `edit_interaction` fire.

## Environment variables (`backend/.env`)

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=gemma2-9b-it
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hcp_crm
```

## Notes / assumptions

- Chat history is kept in-memory per session for this demo; a production
  version would persist it (e.g. Redis) and tie sessions to authenticated
  reps.
- `llama-3.3-70b-versatile` can be swapped in via `GROQ_MODEL` for higher
  reasoning quality on `edit_interaction`'s diff step if needed.
- Font is Google Inter, loaded via `index.html` and applied globally in
  `src/index.css`.
