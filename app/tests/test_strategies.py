# tests/test_strategies.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.api.auth import create_access_token
from app.models.user import User
from app.db.database import get_db

@pytest.fixture
def test_user():
    return User(id=1, email="test@example.com", username="testuser")

@pytest.fixture
def access_token(test_user):
    return create_access_token(data={"sub": test_user.email})

@pytest.fixture
async def authorized_client(access_token):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        ac.headers.update({"Authorization": f"Bearer {access_token}"})
        yield ac

@pytest.fixture
async def test_db():
    # Setup: Create a test database or use a transaction
    db = get_db()
    # TODO: Add any necessary setup for the test database

    yield db

    # Teardown: Clear the test database or rollback the transaction
    # TODO: Add any necessary teardown for the test database

@pytest.mark.asyncio
async def test_create_strategy(authorized_client, test_db, test_user):
    strategy_data = {
        "name": "Test Strategy",
        "description": "A test strategy",
        "is_active": True,
        "components": [
            {
                "component_type": "indicator",
                "parameters": {"type": "SMA", "period": 20}
            },
            {
                "component_type": "entry",
                "parameters": {"condition": "price_above_sma"}
            }
        ],
        "additional_config": {"max_position_size": 1000}
    }

    response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert response.status_code == 200
    created_strategy = response.json()
    assert created_strategy["name"] == strategy_data["name"]
    assert created_strategy["description"] == strategy_data["description"]
    assert created_strategy["is_active"] == strategy_data["is_active"]
    assert len(created_strategy["components"]) == len(strategy_data["components"])
    assert created_strategy["additional_config"] == strategy_data["additional_config"]

@pytest.mark.asyncio
async def test_get_strategies(authorized_client, test_db, test_user):
    # First, create a strategy
    strategy_data = {
        "name": "Test Strategy for Retrieval",
        "description": "A test strategy for retrieval",
        "is_active": True,
        "components": [
            {
                "component_type": "indicator",
                "parameters": {"type": "RSI", "period": 14}
            }
        ],
        "additional_config": {}
    }
    create_response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert create_response.status_code == 200

    # Now, retrieve all strategies
    response = await authorized_client.get("/api/v1/strategies")
    assert response.status_code == 200
    strategies = response.json()
    assert len(strategies) > 0
    assert any(s["name"] == strategy_data["name"] for s in strategies)

@pytest.mark.asyncio
async def test_get_single_strategy(authorized_client, test_db, test_user):
    # First, create a strategy
    strategy_data = {
        "name": "Test Strategy for Single Retrieval",
        "description": "A test strategy for single retrieval",
        "is_active": True,
        "components": [
            {
                "component_type": "exit",
                "parameters": {"condition": "take_profit", "percentage": 5}
            }
        ],
        "additional_config": {"risk_percentage": 1}
    }
    create_response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert create_response.status_code == 200
    created_strategy = create_response.json()

    # Now, retrieve the single strategy
    response = await authorized_client.get(f"/api/v1/strategies/{created_strategy['id']}")
    assert response.status_code == 200
    retrieved_strategy = response.json()
    assert retrieved_strategy["id"] == created_strategy["id"]
    assert retrieved_strategy["name"] == strategy_data["name"]
    assert retrieved_strategy["description"] == strategy_data["description"]
    assert retrieved_strategy["is_active"] == strategy_data["is_active"]
    assert len(retrieved_strategy["components"]) == len(strategy_data["components"])
    assert retrieved_strategy["additional_config"] == strategy_data["additional_config"]

# Add more tests as needed, e.g., for updating and deleting strategies
