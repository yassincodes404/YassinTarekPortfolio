"""CRUD operations for all entities."""

import json
from datetime import datetime, timezone
from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.models import (
    User, Media, Project, Page, Setting, Revision, ActivityLog, generate_uuid, utcnow,
)


# ── Users ─────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password_hash: str, display_name: str = "Admin") -> User:
    user = User(email=email, password_hash=password_hash, display_name=display_name)
    db.add(user)
    await db.flush()
    return user


async def count_users(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(User.id)))
    return result.scalar()


# ── Projects ──────────────────────────────────────────────

async def get_projects(
    db: AsyncSession,
    status: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    offset: int = 0,
    limit: int = 12,
) -> tuple[list[Project], int]:
    """Get paginated projects with optional filters. Returns (projects, total_count)."""
    query = select(Project)
    count_query = select(func.count(Project.id))

    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)

    if search:
        search_filter = or_(
            Project.title.ilike(f"%{search}%"),
            Project.short_description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Project.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    # Filter by tag in Python (JSON field)
    if tag and projects:
        projects = [p for p in projects if tag in (p.tech_stack or [])]
        # Recount
        total = len(projects)

    return list(projects), total


async def get_project_by_slug(db: AsyncSession, slug: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.slug == slug))
    return result.scalar_one_or_none()


async def get_project_by_id(db: AsyncSession, project_id: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def create_project(db: AsyncSession, data: dict) -> Project:
    if not data.get("slug"):
        data["slug"] = slugify(data["title"])
    # Ensure unique slug
    existing = await get_project_by_slug(db, data["slug"])
    if existing:
        data["slug"] = f"{data['slug']}-{generate_uuid()[:8]}"

    project = Project(**data)
    db.add(project)
    await db.flush()
    return project


async def update_project(db: AsyncSession, project: Project, data: dict) -> Project:
    for key, value in data.items():
        if value is not None:
            setattr(project, key, value)
    project.updated_at = utcnow()
    await db.flush()
    return project


async def delete_project(db: AsyncSession, project_id: str) -> bool:
    project = await get_project_by_id(db, project_id)
    if project:
        await db.delete(project)
        await db.flush()
        return True
    return False


async def count_projects(db: AsyncSession, status: str | None = None) -> int:
    query = select(func.count(Project.id))
    if status:
        query = query.where(Project.status == status)
    result = await db.execute(query)
    return result.scalar()


async def get_all_tech_tags(db: AsyncSession) -> list[str]:
    """Get unique tech tags from all projects."""
    result = await db.execute(select(Project.tech_stack))
    all_tags = set()
    for (stack,) in result:
        if stack:
            all_tags.update(stack)
    return sorted(all_tags)


# ── Media ─────────────────────────────────────────────────

async def create_media(db: AsyncSession, data: dict) -> Media:
    media = Media(**data)
    db.add(media)
    await db.flush()
    return media


async def get_media_list(db: AsyncSession, offset: int = 0, limit: int = 24) -> tuple[list[Media], int]:
    total = (await db.execute(select(func.count(Media.id)))).scalar()
    result = await db.execute(
        select(Media).order_by(Media.uploaded_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_media_by_id(db: AsyncSession, media_id: str) -> Media | None:
    result = await db.execute(select(Media).where(Media.id == media_id))
    return result.scalar_one_or_none()


async def delete_media(db: AsyncSession, media_id: str) -> bool:
    media = await get_media_by_id(db, media_id)
    if media:
        await db.delete(media)
        await db.flush()
        return True
    return False


async def count_media(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Media.id)))
    return result.scalar()


# ── Pages ─────────────────────────────────────────────────

async def get_page_by_slug(db: AsyncSession, slug: str) -> Page | None:
    result = await db.execute(select(Page).where(Page.slug == slug))
    return result.scalar_one_or_none()


async def get_page_by_id(db: AsyncSession, page_id: str) -> Page | None:
    result = await db.execute(select(Page).where(Page.id == page_id))
    return result.scalar_one_or_none()


async def get_all_pages(db: AsyncSession) -> list[Page]:
    result = await db.execute(select(Page).order_by(Page.title))
    return list(result.scalars().all())


async def create_page(db: AsyncSession, data: dict) -> Page:
    if not data.get("slug"):
        data["slug"] = slugify(data.get("title", "untitled"))
    page = Page(**data)
    db.add(page)
    await db.flush()
    return page


async def update_page(db: AsyncSession, page: Page, data: dict) -> Page:
    for key, value in data.items():
        if value is not None:
            setattr(page, key, value)
    page.updated_at = utcnow()
    await db.flush()
    return page


# ── Settings ──────────────────────────────────────────────

async def get_setting(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(Setting(key=key, value=value))
    await db.flush()


async def get_all_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(Setting))
    return {s.key: s.value for s in result.scalars().all()}


async def get_settings_json(db: AsyncSession, key: str) -> dict | list | None:
    """Get a setting and parse it as JSON."""
    value = await get_setting(db, key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


# ── Revisions ─────────────────────────────────────────────

async def create_revision(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    snapshot: dict,
    created_by: str | None = None,
) -> Revision:
    rev = Revision(
        entity_type=entity_type,
        entity_id=entity_id,
        snapshot=snapshot,
        created_by=created_by,
    )
    db.add(rev)
    await db.flush()
    return rev


async def get_revisions(
    db: AsyncSession,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 50,
) -> list[Revision]:
    query = select(Revision).order_by(Revision.created_at.desc()).limit(limit)
    if entity_type:
        query = query.where(Revision.entity_type == entity_type)
    if entity_id:
        query = query.where(Revision.entity_id == entity_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_revision_by_id(db: AsyncSession, revision_id: str) -> Revision | None:
    result = await db.execute(select(Revision).where(Revision.id == revision_id))
    return result.scalar_one_or_none()


# ── Activity Log ──────────────────────────────────────────

async def log_activity(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    user_id: str | None = None,
    details: dict | None = None,
):
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_recent_activity(db: AsyncSession, limit: int = 20) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_activity_log(
    db: AsyncSession,
    entity_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[ActivityLog], int]:
    query = select(ActivityLog)
    count_query = select(func.count(ActivityLog.id))

    if entity_type:
        query = query.where(ActivityLog.entity_type == entity_type)
        count_query = count_query.where(ActivityLog.entity_type == entity_type)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
