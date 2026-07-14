from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from app.database import Base, engine, get_db
from app import models, schemas
from app.agent.graph import agent_executor

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM — HCP Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- HCP endpoints ----------

@app.post("/hcps", response_model=schemas.HCPOut)
def create_hcp(hcp: schemas.HCPCreate, db: Session = Depends(get_db)):
    db_hcp = models.HCP(**hcp.model_dump())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp


@app.get("/hcps", response_model=list[schemas.HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(models.HCP).all()


# ---------- Structured form endpoints ----------

@app.post("/interactions", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    interaction = models.Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@app.get("/interactions", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.interaction_date.desc()).all()


@app.put("/interactions/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: str, payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(interaction, key, value)
    db.commit()
    db.refresh(interaction)
    return interaction


# ---------- Conversational (LangGraph agent) endpoint ----------

# naive in-memory chat history per session; fine for a demo/assignment
_chat_sessions: dict[str, list] = {}


@app.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatMessage, session_id: str = "default"):
    history = _chat_sessions.setdefault(session_id, [])
    history.append(HumanMessage(content=payload.message))

    result = agent_executor.invoke({"messages": history})
    history[:] = result["messages"]

    last_ai = next((m for m in reversed(result["messages"]) if isinstance(m, AIMessage)), None)
    reply_text = last_ai.content if last_ai else "Sorry, I couldn't process that."

    tool_used = None
    for m in result["messages"]:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            tool_used = m.tool_calls[-1]["name"]

    return schemas.ChatResponse(reply=reply_text, tool_used=tool_used)


@app.delete("/chat/{session_id}")
def reset_chat(session_id: str = "default"):
    _chat_sessions.pop(session_id, None)
    return {"status": "reset"}
