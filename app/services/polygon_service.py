import asyncio
import websockets
import logging
import json
from app.core.config import settings
from app.db.database import get_db
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolygonWebSocket:
    def __init__(self):
        self.ws_url = "wss://delayed.polygon.io/stocks"
        self.api_key = settings.POLYGON_API_KEY
        logger.info(f"Initialized PolygonWebSocket with API key: {self.api_key[:5]}...")  # Log the first 5 characters of the API key
        self.connection = None
        self.subscribed_symbols = set()

    async def connect(self):
        try:
            self.connection = await websockets.connect(self.ws_url)
            await self.authenticate()
            logger.info("Successfully connected to Polygon WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to Polygon WebSocket: {str(e)}", exc_info=True)
            self.connection = None

    async def authenticate(self):
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        logger.info(f"Sending authentication message: {auth_message}")
        await self.connection.send(json.dumps(auth_message))
        response = await self.connection.recv()
        auth_response = json.loads(response)
        logger.info(f"Received authentication response: {auth_response}")
        
        # Check for successful connection
        if auth_response[0]['status'] == 'connected' and auth_response[0]['message'] == 'Connected Successfully':
            logger.info("Successfully authenticated with Polygon.io")
        else:
            logger.error(f"Authentication failed: {auth_response}")
            raise Exception("Authentication failed")

    async def subscribe(self, symbols):
        if not isinstance(symbols, list):
            symbols = [symbols]
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join([f"A.{symbol}" for symbol in symbols])
        }
        await self.connection.send(json.dumps(subscribe_message))
        self.subscribed_symbols.update(symbols)
        print(f"Subscribed to symbols: {', '.join(symbols)}")

    async def unsubscribe(self, symbols):
        if not isinstance(symbols, list):
            symbols = [symbols]
        
        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ",".join([f"A.{symbol}" for symbol in symbols])
        }
        await self.connection.send(json.dumps(unsubscribe_message))
        self.subscribed_symbols.difference_update(symbols)
        print(f"Unsubscribed from symbols: {', '.join(symbols)}")

    async def store_market_data(self, data):
        db = get_db()
        query = """
        INSERT INTO market_data (asset_id, timestamp, open, high, low, close, volume)
        VALUES (:asset_id, :timestamp, :open, :high, :low, :close, :volume)
        """
        values = {
            "asset_id": await self.get_asset_id(data['sym']),
            "timestamp": datetime.fromtimestamp(data['s'] / 1000),
            "open": data['o'],
            "high": data['h'],
            "low": data['l'],
            "close": data['c'],
            "volume": data['v']
        }
        await db.execute(query, values)

    async def get_asset_id(self, symbol):
        db = get_db()
        query = "SELECT asset_id FROM assets WHERE symbol = :symbol"
        result = await db.fetch_one(query, {"symbol": symbol})
        if result:
            return result['asset_id']
        else:
            # If the asset doesn't exist, create it
            insert_query = "INSERT INTO assets (symbol, name, asset_type) VALUES (:symbol, :symbol, 'stock') RETURNING asset_id"
            result = await db.fetch_one(insert_query, {"symbol": symbol})
            return result['asset_id']

    async def handle_message(self, message):
        logger.info(f"Received message: {message}")
        for data in message:
            if data['ev'] == 'A':  # Aggregate event
                logger.info(f"Received data for {data['sym']}: {data}")
                await self.store_market_data(data)

    async def receive_messages(self):
        while True:
            try:
                message = await self.connection.recv()
                data = json.loads(message)
                await self.handle_message(data)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed. Attempting to reconnect...")
                await self.connect()
                await self.subscribe(list(self.subscribed_symbols))
            except Exception as e:
                logger.error(f"Error in receive_messages: {str(e)}", exc_info=True)

polygon_ws = PolygonWebSocket()

async def initialize_polygon_websocket():
    global polygon_ws
    try:
        await polygon_ws.connect()
        logger.info("Polygon WebSocket initialized and connected")
    except Exception as e:
        logger.error(f"Failed to initialize Polygon WebSocket: {str(e)}", exc_info=True)

async def start_polygon_websocket(symbols):
    if not polygon_ws.connection:
        await initialize_polygon_websocket()
    
    await polygon_ws.subscribe(symbols)
    while True:
        await polygon_ws.receive_messages()

# This function would be called when your application starts
async def run_polygon_websocket():
    symbols = await get_active_symbols()
    if not symbols:
        symbols = ["AAPL", "TSLA", "NVDA"]  # Default symbols for testing
    await start_polygon_websocket(symbols)

async def get_active_symbols():
    db = get_db()
    query = """
    SELECT DISTINCT a.symbol
    FROM assets a
    JOIN strategy_conditions sc ON a.asset_id = sc.asset_id
    JOIN strategies s ON sc.strategy_id = s.strategy_id
    WHERE s.is_active = TRUE
    """
    results = await db.fetch_all(query)
    return [result['symbol'] for result in results]