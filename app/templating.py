"""Template engine setup and site context helper — shared by all routers."""

import json
from pathlib import Path

from fastapi.templating import Jinja2Templates
import markdown

from app.config import settings
from app import crud


# ── Templates ─────────────────────────────────────────────

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ── Custom template filters ──────────────────────────────

def markdown_filter(text):
    """Convert markdown text to HTML."""
    if not text:
        return ""
    return markdown.markdown(text, extensions=["extra", "codehilite", "toc"])


def json_loads_filter(text):
    """Parse JSON string."""
    try:
        return json.loads(text) if isinstance(text, str) else text
    except (json.JSONDecodeError, TypeError):
        return {}


templates.env.filters["markdown"] = markdown_filter
templates.env.filters["json_loads"] = json_loads_filter
templates.env.filters["tojson"] = lambda x: json.dumps(x)


# ── Template context helper ──────────────────────────────

async def get_site_context(db) -> dict:
    """Get common site context for templates."""
    all_settings = await crud.get_all_settings(db)
    css_vars = {}
    try:
        css_vars = json.loads(all_settings.get("css_vars", "{}"))
    except json.JSONDecodeError:
        pass

    social_links = {}
    try:
        social_links = json.loads(all_settings.get("social_links", "{}"))
    except json.JSONDecodeError:
        pass

    # Build WhatsApp link: prefer admin setting, fall back to env var
    whatsapp_raw = social_links.get("whatsapp", "") or ""
    if not whatsapp_raw and settings.WHATSAPP_NUMBER:
        whatsapp_raw = settings.WHATSAPP_NUMBER
    # Auto-convert raw phone numbers to full wa.me URLs
    if whatsapp_raw:
        whatsapp_raw = whatsapp_raw.strip()
        if whatsapp_raw.startswith("http"):
            whatsapp_url = whatsapp_raw
        else:
            # Strip leading +, spaces, dashes from phone number
            clean_number = whatsapp_raw.replace(" ", "").replace("-", "").replace("+", "")
            whatsapp_url = f"https://wa.me/{clean_number}"
    else:
        whatsapp_url = ""

    return {
        "site_title": all_settings.get("site_title", "Portfolio"),
        "site_description": all_settings.get("site_description", ""),
        "analytics_snippet": all_settings.get("analytics_snippet", ""),
        "css_vars": css_vars,
        "social_links": social_links,
        "whatsapp_url": whatsapp_url,
        "contact_email": all_settings.get("contact_email", ""),
        "profile_image_url": all_settings.get("profile_image_url", ""),
    }
