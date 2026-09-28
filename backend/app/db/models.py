"""Chimera-X database models.

Golden rule: provider_id/model_id on Message are HISTORICAL RECORD ONLY.
build_context() must NEVER read them. Context is built purely from conversation_id.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
)
from sqlalchemy.orm import relationship
from app.db.session import Base

IST = timezone(timedelta(hours=5, minutes=30))

def _utcnow():
    return datetime.now(IST)


# ---------------------------------------------------------------------------
# Provider & AIModel — the "mouth" registry
# ---------------------------------------------------------------------------

class Provider(Base):
    """A configured AI provider (cloud or local)."""
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, index=True, nullable=False)  # e.g. "openai", "ollama"
    name = Column(String, nullable=False)                           # Display name
    type = Column(String, nullable=False, default="cloud")          # "local" or "cloud"
    base_url = Column(String, nullable=True)
    api_key = Column(String, nullable=True)                         # Stored locally only
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)                         # Lower = tried first

    # Rate-limit / quota tracking (used by router, Step 2.2)
    is_rate_limited = Column(Boolean, default=False)
    rate_limit_reset_at = Column(DateTime(timezone=True), nullable=True)
    daily_quota_used = Column(Integer, nullable=True, default=0)
    daily_quota_limit = Column(Integer, nullable=True)
    last_reset_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")


class AIModel(Base):
    """A specific model available via a Provider."""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model_name = Column(String, nullable=False)          # LiteLLM identifier e.g. "gpt-4o"
    display_name = Column(String, nullable=True)         # Human-friendly name
    task_tags = Column(JSON, nullable=True)               # e.g. ["code", "chat"]
    size_gb = Column(Float, default=0.0)                  # For hardware constraints
    context_window = Column(Integer, default=8192)       # Max token limit
    is_active = Column(Boolean, default=True)

    # Relationships
    provider = relationship("Provider", back_populates="models")


# ---------------------------------------------------------------------------
# Conversation / Chat — the "brain"
# ---------------------------------------------------------------------------

class Chat(Base):
    """A conversation thread."""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="chats")


class Message(Base):
    """A single message in a conversation.
    
    provider_id and model_id are DISPLAY METADATA ONLY.
    They record which provider generated THIS reply.
    They must NEVER be read by build_context().
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)  # = conversation_id
    role = Column(String, nullable=False)   # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Historical record only — display metadata ("via Claude")
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    chat = relationship("Chat", back_populates="messages")


class Memory(Base):
    """Long-term memory storage for the Brain.
    
    Memories are scoped to a conversation, NEVER to a provider/model.
    """
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chats.id"), nullable=True)  # Scoped to conversation
    key = Column(String, index=True, nullable=False)   # e.g. "coding_style", "user_os"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# Project & Document — organizational grouping
# ---------------------------------------------------------------------------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    chats = relationship("Chat", back_populates="project")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text)  # Extracted text
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store array as JSON for SQLite

    document = relationship("Document", back_populates="chunks")

# ---------------------------------------------------------------------------
# Phase 4 Additions: Tools, Prompts, and Logging
# ---------------------------------------------------------------------------

class PromptTemplate(Base):
    """Conversation-agnostic prompt templates."""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Tool(Base):
    """Registered tools for function calling."""
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    input_schema = Column(JSON, nullable=False) # JSON schema for the tool
    handler_type = Column(String, nullable=False) # e.g. "python_function", "http"
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)


class RouterLog(Base):
    """Log of router decisions, fallbacks, and latencies."""
    __tablename__ = "router_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider_from_id = Column(Integer, ForeignKey("providers.id"), nullable=True) # If it fell back FROM here
    provider_to_id = Column(Integer, ForeignKey("providers.id"), nullable=False)   # The one that actually attempted
    reason = Column(String, nullable=True) # e.g. "quota_exceeded", "initial"
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    task_type = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Incremental Learning (Continuous Finetuning)
# ---------------------------------------------------------------------------

class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)
    content = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False, default=100) # 0-100 scale
    provenance = Column(String, nullable=False, default="model") # 'model' or 'human'
    status = Column(String, nullable=False, default="pending") # 'pending', 'approved', 'rejected'
    created_at = Column(DateTime(timezone=True), default=_utcnow)

class SkillEdge(Base):
    __tablename__ = "skill_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("skill_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("skill_nodes.id"), nullable=False)
    relationship = Column(String, nullable=False) # e.g. "CORRECTS", "DERIVED_FROM"

# ---------------------------------------------------------------------------
# Phase 5 Additions: Life Intelligence (Universal Knowledge Graph)
# ---------------------------------------------------------------------------

class Entity(Base):
    """A node in the Universal Knowledge Graph."""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True, nullable=False) # e.g., "Java", "Become AI Engineer"
    type = Column(String, index=True, nullable=False) # e.g., "Goal", "Skill", "Person", "Project"
    attributes = Column(JSON, nullable=True)          # e.g., {"proficiency": "intermediate"}
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    relations_out = relationship("Relation", foreign_keys="[Relation.source_id]", back_populates="source", cascade="all, delete-orphan")
    relations_in = relationship("Relation", foreign_keys="[Relation.target_id]", back_populates="target", cascade="all, delete-orphan")


class Relation(Base):
    """An edge between two entities in the Universal Knowledge Graph."""
    __tablename__ = "relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    relation_type = Column(String, index=True, nullable=False) # e.g., "REQUIRES", "WORKS_WITH"
    weight = Column(Integer, default=100)                      # Confidence/importance (0-100)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    source = relationship("Entity", foreign_keys=[source_id], back_populates="relations_out")
    target = relationship("Entity", foreign_keys=[target_id], back_populates="relations_in")


class Agent(Base):
    """Dynamic specialized sub-agents."""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g., "Backend Architect"
    system_prompt = Column(Text, nullable=False)
    tools_allowed = Column(JSON, nullable=True) # JSON array of Tool IDs
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Skill(Base):
    """Dynamic discrete skills."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
