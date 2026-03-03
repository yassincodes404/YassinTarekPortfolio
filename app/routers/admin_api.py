"""Admin JSON API routes — used by HTMX and Alpine.js for CRUD operations."""

import json
from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud
from app.auth import require_admin
from app.media import validate_upload, save_upload, delete_upload
from app.cache import cache_clear

router = APIRouter(prefix="/admin/api", tags=["admin-api"])


# ── Projects CRUD ─────────────────────────────────────────

@router.post("/projects")
async def create_project(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    # Handle metadata alias
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")

    # Sanitize FK fields — empty strings violate foreign key constraints
    for fk_field in ("cover_media_id", "video_media_id"):
        if fk_field in data and not data[fk_field]:
            data[fk_field] = None

    # Clean gallery list — remove empty strings
    if "gallery" in data and isinstance(data["gallery"], list):
        data["gallery"] = [g for g in data["gallery"] if g]

    project = await crud.create_project(db, data)
    cache_clear()

    await crud.log_activity(
        db, action="created", entity_type="project",
        entity_id=project.id, user_id=user_id,
        details={"title": project.title},
    )

    return {"id": project.id, "slug": project.slug, "status": "created"}


@router.put("/projects/{project_id}")
async def update_project(
    request: Request,
    project_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = await crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = await request.json()
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")

    # Sanitize FK fields — empty strings violate foreign key constraints
    for fk_field in ("cover_media_id", "video_media_id"):
        if fk_field in data and not data[fk_field]:
            data[fk_field] = None

    # Clean gallery list — remove empty strings
    if "gallery" in data and isinstance(data["gallery"], list):
        data["gallery"] = [g for g in data["gallery"] if g]

    old_status = project.status

    # Create revision before updating
    snapshot = {
        "title": project.title, "slug": project.slug,
        "short_description": project.short_description,
        "full_description": project.full_description,
        "problem_statement": project.problem_statement,
        "tech_stack": project.tech_stack, "status": project.status,
        "video_embed_url": project.video_embed_url,
        "gallery": project.gallery, "metadata": project.metadata_,
    }

    # Only snapshot on publish or significant changes
    if data.get("status") == "published" or old_status == "published":
        await crud.create_revision(db, "project", project.id, snapshot, created_by=user_id)

    await crud.update_project(db, project, data)
    cache_clear()

    action = "published" if data.get("status") == "published" and old_status != "published" else "updated"
    await crud.log_activity(
        db, action=action, entity_type="project",
        entity_id=project.id, user_id=user_id,
        details={"title": project.title},
    )

    return {"id": project.id, "status": "updated"}


@router.delete("/projects/{project_id}")
async def delete_project(
    request: Request,
    project_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = await crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    title = project.title
    await crud.delete_project(db, project_id)
    cache_clear()

    await crud.log_activity(
        db, action="deleted", entity_type="project",
        entity_id=project_id, user_id=user_id,
        details={"title": title},
    )

    return {"status": "deleted"}


# ── Media ─────────────────────────────────────────────────

@router.post("/media/upload")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    error = validate_upload(file.filename, content_type, len(content))
    if error:
        raise HTTPException(status_code=400, detail=error)

    file_info = save_upload(content, file.filename, content_type)
    media = await crud.create_media(db, file_info)

    await crud.log_activity(
        db, action="uploaded", entity_type="media",
        entity_id=media.id, user_id=user_id,
        details={"filename": media.original_filename},
    )

    return {
        "id": media.id,
        "url": media.url,
        "thumbnail_url": media.thumbnail_url,
        "filename": media.original_filename,
    }


@router.delete("/media/{media_id}")
async def delete_media_item(
    request: Request,
    media_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    media = await crud.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    delete_upload(media.filename)
    await crud.delete_media(db, media_id)

    await crud.log_activity(
        db, action="deleted", entity_type="media",
        entity_id=media_id, user_id=user_id,
        details={"filename": media.original_filename},
    )

    return {"status": "deleted"}


@router.get("/media")
async def list_media(
    request: Request,
    page: int = 1,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    per_page = 24
    offset = (page - 1) * per_page
    media_list, total = await crud.get_media_list(db, offset=offset, limit=per_page)
    return {
        "items": [
            {
                "id": m.id, "url": m.url, "thumbnail_url": m.thumbnail_url,
                "filename": m.original_filename, "mime": m.mime,
                "size_bytes": m.size_bytes,
            }
            for m in media_list
        ],
        "total": total,
    }


# ── Pages ─────────────────────────────────────────────────

@router.post("/pages")
async def create_page(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    if "status" not in data or not data["status"]:
        data["status"] = "draft"
    
    page = await crud.create_page(db, data)
    cache_clear()

    await crud.log_activity(
        db, action="created", entity_type="page",
        entity_id=page.id, user_id=user_id,
        details={"title": page.title},
    )

    return {"id": page.id, "slug": page.slug, "status": "created"}


@router.put("/pages/{page_id}")
async def update_page(
    request: Request,
    page_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    page = await crud.get_page_by_id(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    data = await request.json()
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")

    # Create revision
    await crud.create_revision(db, "page", page.id, {
        "title": page.title, "blocks": page.blocks, "status": page.status,
    }, created_by=user_id)

    await crud.update_page(db, page, data)
    cache_clear()

    await crud.log_activity(
        db, action="updated", entity_type="page",
        entity_id=page.id, user_id=user_id,
        details={"title": page.title},
    )

    return {"id": page.id, "status": "updated"}


# ── Settings ──────────────────────────────────────────────

@router.put("/settings")
async def update_settings(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    for key, value in data.items():
        await crud.set_setting(db, key, value)

    cache_clear()

    await crud.log_activity(
        db, action="settings_updated", entity_type="settings",
        user_id=user_id,
    )

    return {"status": "saved"}


# ── Revisions ─────────────────────────────────────────────

@router.post("/revisions/{revision_id}/restore")
async def restore_revision(
    request: Request,
    revision_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    revision = await crud.get_revision_by_id(db, revision_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    snapshot = revision.snapshot

    if revision.entity_type == "project":
        project = await crud.get_project_by_id(db, revision.entity_id)
        if project:
            # Handle metadata alias
            restore_data = dict(snapshot)
            if "metadata" in restore_data:
                restore_data["metadata_"] = restore_data.pop("metadata")
            await crud.update_project(db, project, restore_data)
    elif revision.entity_type == "page":
        page = await crud.get_page_by_id(db, revision.entity_id)
        if page:
            await crud.update_page(db, page, snapshot)

    cache_clear()

    await crud.log_activity(
        db, action="restored", entity_type=revision.entity_type,
        entity_id=revision.entity_id, user_id=user_id,
        details={"revision_id": revision_id},
    )

    return {"status": "restored"}


# ── Import ────────────────────────────────────────────────

@router.post("/import")
async def import_data(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()

    # Import settings
    for key, value in data.get("settings", {}).items():
        await crud.set_setting(db, key, value)

    # Import pages
    for page_data in data.get("pages", []):
        existing = await crud.get_page_by_slug(db, page_data.get("slug", ""))
        if existing:
            await crud.update_page(db, existing, page_data)
        else:
            await crud.create_page(db, page_data)

    # Import projects
    for proj_data in data.get("projects", []):
        if "metadata" in proj_data:
            proj_data["metadata_"] = proj_data.pop("metadata")
        existing = await crud.get_project_by_slug(db, proj_data.get("slug", ""))
        if existing:
            await crud.update_project(db, existing, proj_data)
        else:
            await crud.create_project(db, proj_data)

    cache_clear()

    await crud.log_activity(
        db, action="imported", entity_type="system", user_id=user_id,
    )

    return {"status": "imported"}
