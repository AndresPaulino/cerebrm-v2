import pytest
from app.main import app
from app.db.database import get_db
from app.core.config import settings
import asyncio
from supabase import create_client, Client

@pytest.fixture(scope="session")
async def test_db():
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    yield supabase

@pytest.fixture(autouse=True)
def override_dependency(test_db):
    app.dependency_overrides[get_db] = lambda: test_db