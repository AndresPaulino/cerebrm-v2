# app/db/database.py
from supabase import create_client, Client
from app.core.config import settings
from functools import lru_cache

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@lru_cache()
def get_db():
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return supabase