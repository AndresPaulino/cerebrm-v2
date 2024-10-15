# app/services/schwab_service.py

from app.api.schwab_api.client import Client
from app.db.database import get_db

async def get_schwab_credentials(user_id: int):
    db = get_db()
    credentials = await db.fetch_one(
        "SELECT * FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
        {"user_id": user_id}
    )
    if not credentials:
        raise ValueError("Schwab credentials not found for this user")
    return credentials

def initialize_schwab_client(user_id: int, api_key: str, api_secret: str, callback_url: str):
    return Client(user_id, api_key, api_secret, callback_url)

async def execute_trade(client: Client, account_hash: str, order: dict):
    response = client.order_place(account_hash, order)
    if response.ok:
        order_id = response.headers.get('location', '/').split('/')[-1]
        return {"status": "success", "order_id": order_id}
    else:
        raise Exception(f"Trade execution failed: {response.text}")

async def get_account_positions(client: Client, account_hash: str):
    response = client.account_details(account_hash, fields="positions")
    if response.ok:
        return response.json()
    else:
        raise Exception(f"Failed to get account positions: {response.text}")

async def get_account_orders(client: Client, account_hash: str, from_date: str, to_date: str):
    response = client.account_orders(account_hash, from_date, to_date)
    if response.ok:
        return response.json()
    else:
        raise Exception(f"Failed to get account orders: {response.text}")

async def cancel_order(client: Client, account_hash: str, order_id: str):
    response = client.order_cancel(account_hash, order_id)
    if response.ok:
        return {"status": "success", "message": "Order cancelled successfully"}
    else:
        raise Exception(f"Failed to cancel order: {response.text}")

# Add more methods as needed for other Schwab API functionalities