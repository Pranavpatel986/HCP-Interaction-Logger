import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    territory = Column(String(255))
    hospital = Column(String(255))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(100))  # e.g. "In-person visit", "Call", "Email"
    interaction_date = Column(DateTime, default=datetime.utcnow)
    products_discussed = Column(Text)  # comma separated / JSON string
    samples_provided = Column(Text)
    hcp_sentiment = Column(String(50))  # Positive / Neutral / Negative
    notes = Column(Text)
    summary = Column(Text)  # LLM-generated summary
    follow_up_needed = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)

    source = Column(String(20), default="form")  # "form" or "chat"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    interaction_id = Column(String(36), ForeignKey("interactions.id"), nullable=False)
    due_date = Column(DateTime)
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending / done
    created_at = Column(DateTime, default=datetime.utcnow)
