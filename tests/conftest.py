"""Test configuration and fixtures."""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Set test env vars before importing app
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_EMAIL"] = "admin@test.com"
os.environ["ADMIN_PASSWORD"] = "TestPass123!"
os.environ["DATA_DIR"] = "./test_data"
os.environ["UPLOAD_DIR"] = "./test_data/uploads"

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs():
    """Create test directories."""
    os.makedirs("./test_data/uploads", exist_ok=True)
    yield
    # Cleanup after tests
    import shutil
    if os.path.exists("./test_data"):
        shutil.rmtree("./test_data", ignore_errors=True)


@pytest_asyncio.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
