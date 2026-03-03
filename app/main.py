"""FastAPI application entry point."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, async_session
from app.models import Base
from app.auth import hash_password
from app import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed admin user if none exists
    async with async_session() as db:
        user_count = await crud.count_users(db)
        if user_count == 0:
            await crud.create_user(
                db,
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                display_name="Admin",
            )
            await db.commit()

        # Seed default pages if none exist
        home = await crud.get_page_by_slug(db, "home")
        if not home:
            await crud.create_page(db, {
                "slug": "home",
                "title": "Home",
                "status": "published",
                "blocks": [
                    {
                        "id": "b-hero-1",
                        "type": "hero",
                        "props": {
                            "title": "Hi, I'm Yassin",
                            "subtitle": "Full-Stack Developer & Creative Problem Solver",
                            "cta": [{"label": "View Projects", "href": "/projects"}],
                        },
                        "styles": {},
                    },
                    {
                        "id": "b-grid-1",
                        "type": "project_grid",
                        "props": {"columns": 3, "filterTags": []},
                        "styles": {},
                    },
                ],
            })
            await db.commit()

        about = await crud.get_page_by_slug(db, "about")
        if not about:
            await crud.create_page(db, {
                "slug": "about",
                "title": "About",
                "status": "published",
                "blocks": [
                    {
                        "id": "b-text-1",
                        "type": "text_block",
                        "props": {
                            "content": "# About Me\n\nWelcome to my portfolio. I'm a passionate developer who loves building creative solutions to complex problems.\n\n## Skills\n- **Backend**: Python, FastAPI, Django, Node.js\n- **Frontend**: React, Vue.js, HTMX\n- **Database**: PostgreSQL, SQLite, Redis\n- **DevOps**: Docker, CI/CD, Cloud Deployment",
                        },
                        "styles": {},
                    },
                ],
            })
            await db.commit()

        contact = await crud.get_page_by_slug(db, "contact")
        if not contact:
            await crud.create_page(db, {
                "slug": "contact",
                "title": "Contact",
                "status": "published",
                "blocks": [
                    {
                        "id": "b-text-2",
                        "type": "text_block",
                        "props": {
                            "content": "# Get In Touch\n\nFeel free to reach out if you have a project idea, want to collaborate, or just want to say hello!",
                        },
                        "styles": {},
                    },
                ],
            })
            await db.commit()

        # Seed default settings if none exist
        existing_settings = await crud.get_all_settings(db)
        defaults = {
            "site_title": "Yassin's Portfolio",
            "site_description": "Full-Stack Developer Portfolio",
            "profile_photo_id": "",
            "contact_email": "",
            "social_links": json.dumps({"github": "", "linkedin": "", "twitter": ""}),
            "analytics_snippet": "",
            "css_vars": json.dumps({
                "accent_color": "#6366f1",
                "accent_color_hover": "#4f46e5",
                "font_heading": "Inter",
                "font_body": "Inter",
            }),
        }
        for k, v in defaults.items():
            if k not in existing_settings:
                await crud.set_setting(db, k, v)
        await db.commit()

    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    yield  # App runs here

    # Shutdown
    await engine.dispose()


# ── Create App ────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# ── Mount static files ────────────────────────────────────

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount uploads (served from persistent volume)
upload_dir = settings.upload_path
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# ── Include routers ──────────────────────────────────────

from app.routers.health import router as health_router
from app.routers.public import router as public_router
from app.routers.admin import router as admin_router
from app.routers.admin_api import router as admin_api_router

app.include_router(health_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(admin_api_router)
