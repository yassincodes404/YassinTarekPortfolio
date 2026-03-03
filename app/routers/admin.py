"""Admin HTML routes — renders admin pages with session auth."""

import json
import math
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud
from app.auth import (
    verify_password, create_session_token, require_admin,
    SESSION_COOKIE_NAME, SESSION_MAX_AGE, get_session_user_id,
)
from app.templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Login / Logout ────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in, redirect to dashboard
    if get_session_user_id(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await crud.get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Invalid email or password.",
        })

    token = create_session_token(user.id)
    await crud.log_activity(db, action="login", entity_type="user", user_id=user.id)

    response = RedirectResponse(url="/admin", status_code=302)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="strict",
        secure=False,  # Set to True in production behind HTTPS
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


# ── Dashboard ─────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = {
        "published_projects": await crud.count_projects(db, status="published"),
        "draft_projects": await crud.count_projects(db, status="draft"),
        "media_count": await crud.count_media(db),
        "pages_count": len(await crud.get_all_pages(db)),
    }
    recent_activity = await crud.get_recent_activity(db, limit=10)

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "stats": stats,
        "recent_activity": recent_activity,
    })


# ── Projects ──────────────────────────────────────────────

@router.get("/projects", response_class=HTMLResponse)
async def projects_list(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    projects, _ = await crud.get_projects(db, limit=100)
    return templates.TemplateResponse("admin/projects_list.html", {
        "request": request,
        "active_page": "projects",
        "projects": projects,
    })


@router.get("/projects/new", response_class=HTMLResponse)
async def project_new(
    request: Request,
    user_id: str = Depends(require_admin),
):
    return templates.TemplateResponse("admin/project_form.html", {
        "request": request,
        "active_page": "projects",
        "project": None,
        "project_json": "{}",
    })


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def project_edit(
    request: Request,
    project_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    project = await crud.get_project_by_id(db, project_id)
    if not project:
        return RedirectResponse(url="/admin/projects", status_code=302)

    project_data = {
        "id": project.id,
        "title": project.title,
        "slug": project.slug,
        "short_description": project.short_description,
        "full_description": project.full_description,
        "problem_statement": project.problem_statement,
        "tech_stack": project.tech_stack or [],
        "cover_media_id": project.cover_media_id or "",
        "video_media_id": project.video_media_id or "",
        "video_embed_url": project.video_embed_url or "",
        "gallery": project.gallery or [],
        "metadata": project.metadata_ or {},
        "status": project.status,
    }

    return templates.TemplateResponse("admin/project_form.html", {
        "request": request,
        "active_page": "projects",
        "project": project,
        "project_json": json.dumps(project_data),
    })


# ── Media Library ─────────────────────────────────────────

@router.get("/media", response_class=HTMLResponse)
async def media_library(
    request: Request,
    page: int = 1,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    per_page = 24
    offset = (page - 1) * per_page
    media_list, total = await crud.get_media_list(db, offset=offset, limit=per_page)
    total_pages = max(1, math.ceil(total / per_page))

    return templates.TemplateResponse("admin/media_library.html", {
        "request": request,
        "active_page": "media",
        "media_list": media_list,
        "page": page,
        "total_pages": total_pages,
    })


# ── Pages ─────────────────────────────────────────────────

@router.get("/pages", response_class=HTMLResponse)
async def pages_list(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pages = await crud.get_all_pages(db)
    return templates.TemplateResponse("admin/pages_list.html", {
        "request": request,
        "active_page": "pages",
        "pages": pages,
    })


@router.get("/pages/{page_id}/edit", response_class=HTMLResponse)
async def page_edit(
    request: Request,
    page_id: str,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    page = await crud.get_page_by_id(db, page_id)
    if not page:
        return RedirectResponse(url="/admin/pages", status_code=302)

    return templates.TemplateResponse("admin/page_builder.html", {
        "request": request,
        "active_page": "pages",
        "page": page,
        "blocks_json": json.dumps(page.blocks or []),
    })


# ── Settings ──────────────────────────────────────────────

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    all_settings = await crud.get_all_settings(db)
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "active_page": "settings",
        "settings_json": json.dumps(all_settings),
    })


# ── Revisions ─────────────────────────────────────────────

@router.get("/revisions", response_class=HTMLResponse)
async def revisions_page(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    revisions = await crud.get_revisions(db, limit=50)
    return templates.TemplateResponse("admin/revisions.html", {
        "request": request,
        "active_page": "revisions",
        "revisions": revisions,
    })


# ── Activity Log ──────────────────────────────────────────

@router.get("/activity", response_class=HTMLResponse)
async def activity_page(
    request: Request,
    page: int = 1,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    per_page = 50
    offset = (page - 1) * per_page
    activities, total = await crud.get_activity_log(db, offset=offset, limit=per_page)
    total_pages = max(1, math.ceil(total / per_page))

    return templates.TemplateResponse("admin/activity_log.html", {
        "request": request,
        "active_page": "activity",
        "activities": activities,
        "page": page,
        "total_pages": total_pages,
    })


# ── Export ────────────────────────────────────────────────

@router.get("/export")
async def export_data(
    request: Request,
    user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Export all content as JSON."""
    projects, _ = await crud.get_projects(db, limit=1000)
    pages = await crud.get_all_pages(db)
    all_settings = await crud.get_all_settings(db)
    media_list, _ = await crud.get_media_list(db, limit=10000)

    export = {
        "projects": [
            {
                "id": p.id, "slug": p.slug, "title": p.title,
                "short_description": p.short_description,
                "full_description": p.full_description,
                "problem_statement": p.problem_statement,
                "tech_stack": p.tech_stack, "status": p.status,
                "video_embed_url": p.video_embed_url,
                "gallery": p.gallery, "metadata": p.metadata_,
            }
            for p in projects
        ],
        "pages": [
            {"id": p.id, "slug": p.slug, "title": p.title, "blocks": p.blocks, "status": p.status}
            for p in pages
        ],
        "settings": all_settings,
        "media": [
            {"id": m.id, "filename": m.filename, "url": m.url, "mime": m.mime}
            for m in media_list
        ],
    }

    return JSONResponse(content=export, headers={
        "Content-Disposition": "attachment; filename=portfolio-export.json"
    })
