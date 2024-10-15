import asyncio
from app.db.database import get_db
from datetime import datetime, timedelta

async def cleanup_old_data():
    db = get_db()
    retention_days = 30  # Adjust as needed
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    query = """
    DELETE FROM market_data
    WHERE time < :cutoff_date
    """
    await db.execute(query, {"cutoff_date": cutoff_date})

# This function should be scheduled to run daily
async def schedule_cleanup():
    while True:
        await cleanup_old_data()
        await asyncio.sleep(24 * 60 * 60)  # Sleep for 24 hours