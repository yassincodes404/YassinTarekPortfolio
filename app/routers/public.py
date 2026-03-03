"""Public-facing HTML routes."""

import math
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud
from app.templating import templates, get_site_context

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    """Render home page with dynamic blocks."""
    site_ctx = await get_site_context(db)
    page = await crud.get_page_by_slug(db, "home")
    blocks = page.blocks if page else []

    # If there's a project_grid block, fetch published projects
    projects = []
    for block in blocks:
        if block.get("type") == "project_grid":
            proj_list, _ = await crud.get_projects(db, status="published", limit=6)
            # Eagerly load cover media and video media
            for p in proj_list:
                if p.cover_media_id:
                    p.cover_media = await crud.get_media_by_id(db, p.cover_media_id)
                if p.video_media_id:
                    p.video_media = await crud.get_media_by_id(db, p.video_media_id)
            projects = proj_list
            break

    return templates.TemplateResponse("public/home.html", {
        "request": request,
        **site_ctx,
        "blocks": blocks,
        "projects": projects,
        "now": datetime.now(timezone.utc),
    })


@router.get("/projects", response_class=HTMLResponse)
async def projects_list(
    request: Request,
    page: int = 1,
    q: str = "",
    tag: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Render paginated projects list with search and tag filter."""
    site_ctx = await get_site_context(db)
    per_page = 12
    offset = (page - 1) * per_page

    projects, total = await crud.get_projects(
        db, status="published", search=q or None, tag=tag or None,
        offset=offset, limit=per_page,
    )

    # Load cover media and video media for each project
    for p in projects:
        if p.cover_media_id:
            p.cover_media = await crud.get_media_by_id(db, p.cover_media_id)
        if p.video_media_id:
            p.video_media = await crud.get_media_by_id(db, p.video_media_id)

    total_pages = max(1, math.ceil(total / per_page))
    all_tags = await crud.get_all_tech_tags(db)

    return templates.TemplateResponse("public/projects.html", {
        "request": request,
        **site_ctx,
        "projects": projects,
        "page": page,
        "total_pages": total_pages,
        "search": q,
        "current_tag": tag,
        "tags": all_tags,
        "now": datetime.now(timezone.utc),
    })


@router.get("/projects/{slug}", response_class=HTMLResponse)
async def project_detail(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    """Render project detail page."""
    site_ctx = await get_site_context(db)
    project = await crud.get_project_by_slug(db, slug)

    if not project or project.status != "published":
        return templates.TemplateResponse("public/projects.html", {
            "request": request,
            **site_ctx,
            "projects": [],
            "page": 1,
            "total_pages": 1,
            "search": "",
            "current_tag": "",
            "tags": [],
            "now": datetime.now(timezone.utc),
        })

    # Load media
    if project.cover_media_id:
        project.cover_media = await crud.get_media_by_id(db, project.cover_media_id)
    if project.video_media_id:
        project.video_media = await crud.get_media_by_id(db, project.video_media_id)

    gallery_media = []
    if project.gallery:
        for media_id in project.gallery:
            m = await crud.get_media_by_id(db, media_id)
            if m:
                gallery_media.append(m)

    return templates.TemplateResponse("public/project_detail.html", {
        "request": request,
        **site_ctx,
        "project": project,
        "gallery_media": gallery_media,
        "now": datetime.now(timezone.utc),
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, db: AsyncSession = Depends(get_db)):
    """Render about page."""
    site_ctx = await get_site_context(db)
    page = await crud.get_page_by_slug(db, "about")
    blocks = page.blocks if page else []

    return templates.TemplateResponse("public/about.html", {
        "request": request,
        **site_ctx,
        "blocks": blocks,
        "now": datetime.now(timezone.utc),
    })


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, message: str = "", db: AsyncSession = Depends(get_db)):
    """Render contact page."""
    site_ctx = await get_site_context(db)
    page = await crud.get_page_by_slug(db, "contact")
    blocks = page.blocks if page else []

    return templates.TemplateResponse("public/contact.html", {
        "request": request,
        **site_ctx,
        "blocks": blocks,
        "message": message,
        "now": datetime.now(timezone.utc),
    })


@router.post("/contact")
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle contact form submission."""
    # Log the contact submission as activity
    await crud.log_activity(
        db,
        action="contact_form",
        entity_type="contact",
        details={"name": name, "email": email, "subject": subject, "message": message},
    )

    return RedirectResponse(
        url="/contact?message=Thank+you+for+your+message!+I'll+get+back+to+you+soon.",
        status_code=303,
    )
