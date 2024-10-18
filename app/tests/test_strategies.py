# tests/test_strategy_creation.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.api.auth import create_access_token
from app.models.user import User

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

async def test_create_simple_strategy(authorized_client):
    strategy_data = {
        "name": "Simple Stock Strategy",
        "description": "Buy a stock if price changes by 5%",
        "is_active": True,
        "asset_filters": [
            {
                "type": "symbol",
                "value": "AAPL"
            }
        ],
        "components": [
            {
                "component_type": "entry",
                "conditions": [
                    {
                        "type": "price_change",
                        "comparison": "greater_than",
                        "value": 5
                    }
                ],
                "parameters": {"action": "buy"}
            },
            {
                "component_type": "exit",
                "exit_conditions": [
                    {
                        "type": "take_profit",
                        "value": 10
                    },
                    {
                        "type": "stop_loss",
                        "value": 5
                    }
                ],
                "parameters": {"action": "sell"}
            }
        ],
        "additional_config": {"position_size": 100}
    }

    response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert response.status_code == 200
    created_strategy = response.json()
    assert created_strategy["name"] == strategy_data["name"]
    assert len(created_strategy["components"]) == 2

async def test_create_multi_asset_strategy(authorized_client):
    strategy_data = {
        "name": "Multi-Asset Strategy",
        "description": "Trade multiple tech stocks",
        "is_active": True,
        "asset_filters": [
            {
                "type": "sector",
                "value": "Technology"
            },
            {
                "type": "market_cap",
                "value": {"min": 1000000000}  # $1B minimum market cap
            }
        ],
        "components": [
            {
                "component_type": "entry",
                "conditions": [
                    {
                        "type": "technical_indicator",
                        "indicator": "RSI",
                        "comparison": "less_than",
                        "value": 30
                    }
                ],
                "parameters": {"action": "buy"}
            },
            {
                "component_type": "exit",
                "exit_conditions": [
                    {
                        "type": "technical_indicator",
                        "indicator": "RSI",
                        "comparison": "greater_than",
                        "value": 70
                    }
                ],
                "parameters": {"action": "sell"}
            }
        ],
        "additional_config": {"max_positions": 5, "position_size_percentage": 20}
    }

    response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert response.status_code == 200
    created_strategy = response.json()
    assert created_strategy["name"] == strategy_data["name"]
    assert len(created_strategy["asset_filters"]) == 2

async def test_create_complex_strategy(authorized_client):
    strategy_data = {
        "name": "Complex Trading Strategy",
        "description": "Multiple conditions and custom indicator",
        "is_active": True,
        "asset_filters": [
            {
                "type": "custom_list",
                "value": ["AAPL", "GOOGL", "MSFT", "AMZN"]
            }
        ],
        "components": [
            {
                "component_type": "entry",
                "conditions": [
                    {
                        "type": "technical_indicator",
                        "indicator": "SMA",
                        "comparison": "crosses_above",
                        "value": {"fast_period": 10, "slow_period": 50}
                    },
                    {
                        "type": "technical_indicator",
                        "indicator": "custom_momentum",
                        "comparison": "greater_than",
                        "value": 0
                    },
                    {
                        "type": "time",
                        "comparison": "between",
                        "value": {"start": "09:30", "end": "16:00"}
                    }
                ],
                "parameters": {"action": "buy"}
            },
            {
                "component_type": "exit",
                "exit_conditions": [
                    {
                        "type": "trailing_stop",
                        "value": 5
                    },
                    {
                        "type": "time",
                        "comparison": "equals",
                        "value": "15:55"
                    }
                ],
                "parameters": {"action": "sell"}
            }
        ],
        "additional_config": {
            "risk_per_trade": 1,
            "custom_indicators": [
                {
                    "name": "custom_momentum",
                    "calculation": "(close - close[10]) / close[10] * 100"
                }
            ]
        }
    }

    response = await authorized_client.post("/api/v1/strategies", json=strategy_data)
    assert response.status_code == 200
    created_strategy = response.json()
    assert created_strategy["name"] == strategy_data["name"]
    assert len(created_strategy["components"]) == 2
    assert "custom_indicators" in created_strategy["additional_config"]

# Add more test cases as needed