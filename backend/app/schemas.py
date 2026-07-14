from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    territory: Optional[str] = None
    hospital: Optional[str] = None
    email: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    hcp_id: str
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime] = None
    products_discussed: Optional[str] = None
    samples_provided: Optional[str] = None
    hcp_sentiment: Optional[str] = None
    notes: Optional[str] = None
    follow_up_needed: Optional[bool] = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    source: Optional[str] = "form"


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    interaction_type: Optional[str]
    interaction_date: Optional[datetime]
    products_discussed: Optional[str]
    samples_provided: Optional[str]
    hcp_sentiment: Optional[str]
    notes: Optional[str]
    summary: Optional[str]
    follow_up_needed: Optional[bool]
    follow_up_date: Optional[datetime]
    follow_up_notes: Optional[str]
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str
    hcp_id: Optional[str] = None
    interaction_id: Optional[str] = None  # set when editing via chat


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    interaction: Optional[InteractionOut] = None
