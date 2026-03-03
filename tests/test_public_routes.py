"""Basic tests for public routes and health check."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_home_page(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "Portfolio" in resp.text or "Yassin" in resp.text


@pytest.mark.asyncio
async def test_projects_page(client: AsyncClient):
    resp = await client.get("/projects")
    assert resp.status_code == 200
    assert "Projects" in resp.text


@pytest.mark.asyncio
async def test_about_page(client: AsyncClient):
    resp = await client.get("/about")
    assert resp.status_code == 200
    assert "About" in resp.text


@pytest.mark.asyncio
async def test_contact_page(client: AsyncClient):
    resp = await client.get("/contact")
    assert resp.status_code == 200
    assert "Contact" in resp.text or "Touch" in resp.text


@pytest.mark.asyncio
async def test_admin_login_page(client: AsyncClient):
    resp = await client.get("/admin/login")
    assert resp.status_code == 200
    assert "Sign In" in resp.text or "Login" in resp.text


@pytest.mark.asyncio
async def test_admin_requires_auth(client: AsyncClient):
    resp = await client.get("/admin", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers.get("location", "")
