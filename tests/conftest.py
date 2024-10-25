import pytest
from app.main import app
from app.db.database import get_db
from app.core.config import settings
import asyncio
from supabase import create_client, Client
from httpx import ASGITransport, AsyncClient

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@pytest.fixture(autouse=True)
def override_dependency(test_db):
    app.dependency_overrides[get_db] = lambda: test_db

@pytest.fixture
async def authorized_client(access_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers.update({"Authorization": f"Bearer {access_token}"})
        yield client