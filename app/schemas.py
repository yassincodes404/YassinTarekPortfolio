"""Pydantic schemas for request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ── Projects ──────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = ""
    short_description: str = ""
    full_description: str = ""
    problem_statement: str = ""
    tech_stack: list[str] = []
    cover_media_id: Optional[str] = None
    video_media_id: Optional[str] = None
    video_embed_url: str = ""
    gallery: list[str] = []
    metadata_: dict = Field(default_factory=dict, alias="metadata")
    status: str = "draft"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    problem_statement: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    cover_media_id: Optional[str] = None
    video_media_id: Optional[str] = None
    video_embed_url: Optional[str] = None
    gallery: Optional[list[str]] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    slug: str
    title: str
    short_description: str
    full_description: str
    problem_statement: str
    tech_stack: list[str]
    cover_media_id: Optional[str]
    video_media_id: Optional[str]
    video_embed_url: str
    gallery: list[str]
    metadata_: dict = Field(alias="metadata")
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ── Media ─────────────────────────────────────────────────

class MediaOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    url: str
    mime: str
    size_bytes: int
    thumbnail_url: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Pages ─────────────────────────────────────────────────

class BlockSchema(BaseModel):
    id: str
    type: str  # hero, project_grid, text_block, video_embed, image_banner, two_column, custom_html, achievements
    props: dict = {}
    styles: dict = {}


class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    blocks: Optional[list[dict]] = None
    metadata_: Optional[dict] = Field(default=None, alias="metadata")
    status: Optional[str] = None


class PageOut(BaseModel):
    id: str
    slug: str
    title: str
    blocks: list[dict]
    metadata_: dict = Field(alias="metadata")
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ── Settings ──────────────────────────────────────────────

class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingOut(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True


# ── Revisions ─────────────────────────────────────────────

class RevisionOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    snapshot: dict
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Activity ──────────────────────────────────────────────

class ActivityOut(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True


# ── Auth ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


# ── Export/Import ─────────────────────────────────────────

class ExportData(BaseModel):
    projects: list[dict] = []
    pages: list[dict] = []
    settings: list[dict] = []
    media: list[dict] = []
