"""
Tool implementations for the HCP Interaction LangGraph agent.

Each tool is a plain Python function decorated with @tool so LangGraph's
ToolNode can call it directly. Tools talk to the DB via a fresh SQLAlchemy
session and use the Groq-hosted LLM for extraction/summarization where noted.
"""
import json
from datetime import datetime, timedelta
from typing import Optional

from langchain_core.tools import tool
from langchain_groq import ChatGroq

from app.database import SessionLocal
from app.models import HCP, Interaction, FollowUpTask
import os

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

llm = ChatGroq(model=GROQ_MODEL, temperature=0)


EXTRACTION_PROMPT = """You are an assistant that extracts structured pharma sales
interaction data from a field rep's free-text note. Return ONLY valid JSON with
these keys (use null if unknown):
interaction_type (one of "In-person visit", "Call", "Email", "Conference"),
products_discussed (comma separated string),
samples_provided (comma separated string or null),
hcp_sentiment (one of "Positive", "Neutral", "Negative"),
follow_up_needed (true/false),
follow_up_date (ISO date string or null),
follow_up_notes (string or null),
summary (one sentence summary of the interaction).

Rep's note:
\"\"\"{text}\"\"\"
"""


def _extract_with_llm(text: str) -> dict:
    resp = llm.invoke(EXTRACTION_PROMPT.format(text=text))
    content = resp.content.strip()
    # Groq/gemma sometimes wraps JSON in markdown fences
    if content.startswith("```"):
        content = content.strip("`")
        content = content.split("\n", 1)[-1] if content.lower().startswith("json") else content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "interaction_type": None,
            "products_discussed": None,
            "samples_provided": None,
            "hcp_sentiment": "Neutral",
            "follow_up_needed": False,
            "follow_up_date": None,
            "follow_up_notes": None,
            "summary": text[:200],
        }


@tool
def log_interaction(hcp_id: str, raw_text: str) -> str:
    """Log a new HCP interaction from a rep's free-text description.
    Uses the LLM to extract interaction type, products discussed, samples
    provided, HCP sentiment, and follow-up details, then saves a structured
    record to the database. Returns the created interaction as JSON."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        extracted = _extract_with_llm(raw_text)

        follow_up_date = None
        if extracted.get("follow_up_date"):
            try:
                follow_up_date = datetime.fromisoformat(extracted["follow_up_date"])
            except ValueError:
                follow_up_date = None

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=extracted.get("interaction_type") or "Call",
            interaction_date=datetime.utcnow(),
            products_discussed=extracted.get("products_discussed"),
            samples_provided=extracted.get("samples_provided"),
            hcp_sentiment=extracted.get("hcp_sentiment") or "Neutral",
            notes=raw_text,
            summary=extracted.get("summary"),
            follow_up_needed=bool(extracted.get("follow_up_needed")),
            follow_up_date=follow_up_date,
            follow_up_notes=extracted.get("follow_up_notes"),
            source="chat",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        result = {
            "id": interaction.id,
            "hcp_id": interaction.hcp_id,
            "interaction_type": interaction.interaction_type,
            "products_discussed": interaction.products_discussed,
            "samples_provided": interaction.samples_provided,
            "hcp_sentiment": interaction.hcp_sentiment,
            "summary": interaction.summary,
            "follow_up_needed": interaction.follow_up_needed,
        }
        return json.dumps(result)
    finally:
        db.close()


@tool
def edit_interaction(interaction_id: str, change_request: str) -> str:
    """Edit an existing logged interaction. Given the interaction_id and a
    natural-language description of what should change (e.g. 'change the
    sentiment to Positive and push follow-up to next Friday'), uses the LLM
    to interpret the requested change and updates the record. Returns the
    updated interaction as JSON."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        prompt = f"""You are updating a CRM record. Current record (JSON):
{{
  "interaction_type": "{interaction.interaction_type}",
  "products_discussed": "{interaction.products_discussed}",
  "samples_provided": "{interaction.samples_provided}",
  "hcp_sentiment": "{interaction.hcp_sentiment}",
  "follow_up_needed": {str(interaction.follow_up_needed).lower()},
  "follow_up_date": "{interaction.follow_up_date}",
  "follow_up_notes": "{interaction.follow_up_notes}"
}}

The rep wants this change: "{change_request}"

Return ONLY a JSON object containing just the fields that should change,
with their new values (same keys as above). Use ISO date format for dates."""

        resp = llm.invoke(prompt)
        content = resp.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.split("\n", 1)[-1] if content.lower().startswith("json") else content

        try:
            changes = json.loads(content)
        except json.JSONDecodeError:
            changes = {}

        for key, value in changes.items():
            if key == "follow_up_date" and value:
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    continue
            if hasattr(interaction, key):
                setattr(interaction, key, value)

        interaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "updated_fields": list(changes.keys()),
            "interaction_type": interaction.interaction_type,
            "hcp_sentiment": interaction.hcp_sentiment,
            "follow_up_date": str(interaction.follow_up_date),
        })
    finally:
        db.close()


@tool
def search_hcp_profile(name_or_id: str) -> str:
    """Look up an HCP's profile (specialty, territory, hospital) and their
    recent interaction history by name or ID. Use this before logging an
    interaction to get context about the HCP."""
    db = SessionLocal()
    try:
        hcp = (
            db.query(HCP)
            .filter((HCP.id == name_or_id) | (HCP.name.ilike(f"%{name_or_id}%")))
            .first()
        )
        if not hcp:
            return json.dumps({"error": f"No HCP found matching '{name_or_id}'"})

        recent = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(5)
            .all()
        )
        return json.dumps({
            "id": hcp.id,
            "name": hcp.name,
            "specialty": hcp.specialty,
            "territory": hcp.territory,
            "hospital": hcp.hospital,
            "recent_interactions": [
                {
                    "date": str(i.interaction_date),
                    "type": i.interaction_type,
                    "summary": i.summary,
                }
                for i in recent
            ],
        })
    finally:
        db.close()


@tool
def schedule_follow_up(interaction_id: str, due_date: str, description: str) -> str:
    """Create a follow-up task tied to a logged interaction, e.g. 'send new
    trial data' due on a specific date. due_date should be an ISO date
    string (YYYY-MM-DD)."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        try:
            due = datetime.fromisoformat(due_date)
        except ValueError:
            due = datetime.utcnow() + timedelta(days=7)

        task = FollowUpTask(interaction_id=interaction_id, due_date=due, description=description)
        db.add(task)

        interaction.follow_up_needed = True
        interaction.follow_up_date = due
        interaction.follow_up_notes = description

        db.commit()
        db.refresh(task)

        return json.dumps({
            "task_id": task.id,
            "interaction_id": interaction_id,
            "due_date": str(task.due_date),
            "description": task.description,
        })
    finally:
        db.close()


@tool
def generate_call_prep_summary(hcp_id: str, num_interactions: int = 5) -> str:
    """Generate a short call-prep brief summarizing an HCP's last N
    interactions, so a rep can review it before their next visit. Uses the
    LLM to synthesize the history into a few bullet points."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp_id)
            .order_by(Interaction.interaction_date.desc())
            .limit(num_interactions)
            .all()
        )
        if not interactions:
            return json.dumps({"summary": f"No prior interactions on file for {hcp.name}."})

        history_text = "\n".join(
            f"- {i.interaction_date}: {i.interaction_type}, products: {i.products_discussed}, "
            f"sentiment: {i.hcp_sentiment}, notes: {i.summary}"
            for i in interactions
        )
        prompt = (
            f"Summarize this HCP's interaction history into a short call-prep "
            f"brief (3-5 bullet points) for a field rep about to visit {hcp.name} "
            f"({hcp.specialty}):\n{history_text}"
        )
        resp = llm.invoke(prompt)
        return json.dumps({"hcp": hcp.name, "call_prep_brief": resp.content.strip()})
    finally:
        db.close()


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    search_hcp_profile,
    schedule_follow_up,
    generate_call_prep_summary,
]
