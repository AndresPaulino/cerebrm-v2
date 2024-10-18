import asyncio
import logging
from typing import Optional, Union
from polygon import WebSocketClient, RESTClient
from polygon.websocket.models import Feed, Market, EquityAgg
from app.core.config import settings
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiCallHandler:
    def __init__(self):
        self.api_call_queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor()
        self.client = RESTClient(api_key=settings.POLYGON_API_KEY)

    async def enqueue_api_call(self, symbol):
        await self.api_call_queue.put(symbol)

    async def start_processing_api_calls(self):
        while True:
            symbol = await self.api_call_queue.get()
            try:
                details = await asyncio.get_running_loop().run_in_executor(
                    self.executor, self.get_symbol_details, symbol
                )
                logger.info(f"Symbol details for {symbol}: {details}")
            except Exception as e:
                logger.error(f"Error processing API call for {symbol}: {e}")
            finally:
                self.api_call_queue.task_done()

    def get_symbol_details(self, symbol):
        return self.client.get_ticker_details(symbol)

class MessageHandler:
    def __init__(self, api_call_handler):
        self.handler_queue = asyncio.Queue()
        self.api_call_handler = api_call_handler

    async def add(self, message: Optional[Union[str, bytes, list]]) -> None:
        await self.handler_queue.put(message)

    async def start_handling(self) -> None:
        while True:
            message = await self.handler_queue.get()
            logger.info(f"Received message: {message}")
            try:
                if isinstance(message, list):
                    for msg in message:
                        if isinstance(msg, EquityAgg):
                            logger.info(f"Received data for {msg.symbol}: {msg}")
                            await self.api_call_handler.enqueue_api_call(msg.symbol)
                elif isinstance(message, dict) and message.get("ev") == "status":
                    logger.info(f"Received status message: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
            finally:
                self.handler_queue.task_done()

class PolygonWebSocket:
    def __init__(self):
        self.api_key = settings.POLYGON_API_KEY
        self.client = WebSocketClient(
            api_key=self.api_key,
            feed=Feed.Delayed,
            market=Market.Stocks,
            subscriptions=["A.*"]
        )
        self.api_call_handler = ApiCallHandler()
        self.message_handler = MessageHandler(self.api_call_handler)
        logger.info(f"Initialized PolygonWebSocket with API key: {self.api_key[:5]}...")

    async def start_event_stream(self):
        try:
            await asyncio.gather(
                self.client.connect(self.message_handler.add),
                self.message_handler.start_handling(),
                self.api_call_handler.start_processing_api_calls(),
            )
        except Exception as e:
            logger.error(f"Error in WebSocket stream: {e}")

    async def shutdown(self):
        self.client.close()
        logger.info("Polygon WebSocket connection closed")

polygon_ws = PolygonWebSocket()

async def initialize_polygon_websocket():
    global polygon_ws
    try:
        logger.info("Polygon WebSocket initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Polygon WebSocket: {str(e)}", exc_info=True)

async def run_polygon_websocket():
    await polygon_ws.start_event_stream()

async def shutdown_polygon_websocket():
    await polygon_ws.shutdown()