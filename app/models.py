"""SQLAlchemy ORM models for the portfolio application."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), default="Admin")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    activities = relationship("ActivityLog", back_populates="user")


class Media(Base):
    __tablename__ = "media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)  # relative: /uploads/...
    mime = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=utcnow)

    # Relationships
    cover_projects = relationship(
        "Project", foreign_keys="Project.cover_media_id", back_populates="cover_media"
    )
    video_projects = relationship(
        "Project", foreign_keys="Project.video_media_id", back_populates="video_media"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    short_description = Column(Text, default="")
    full_description = Column(Text, default="")  # markdown/html
    problem_statement = Column(Text, default="")
    tech_stack = Column(JSON, default=list)  # ["Python", "FastAPI", ...]
    cover_media_id = Column(String(36), ForeignKey("media.id"), nullable=True)
    video_media_id = Column(String(36), ForeignKey("media.id"), nullable=True)
    video_embed_url = Column(String(500), default="")  # YouTube/Vimeo embed
    gallery = Column(JSON, default=list)  # list of media IDs
    metadata_ = Column("metadata", JSON, default=dict)  # SEO: {title, description, keywords}
    status = Column(String(20), default="draft", index=True)  # draft / published / archived
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    cover_media = relationship("Media", foreign_keys=[cover_media_id], back_populates="cover_projects")
    video_media = relationship("Media", foreign_keys=[video_media_id], back_populates="video_projects")

    __table_args__ = (
        Index("ix_projects_status_created", "status", "created_at"),
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    blocks = Column(JSON, default=list)  # ordered array of block objects
    metadata_ = Column("metadata", JSON, default=dict)  # SEO
    status = Column(String(20), default="draft")  # draft / published
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, default="")


class Revision(Base):
    __tablename__ = "revisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False, index=True)  # project / page
    entity_id = Column(String(36), nullable=False, index=True)
    snapshot = Column(JSON, nullable=False)  # full JSON snapshot
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("ix_revisions_entity", "entity_type", "entity_id"),
    )


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # created, updated, published, deleted, uploaded, ...
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("ix_activity_entity", "entity_type", "entity_id"),
    )
