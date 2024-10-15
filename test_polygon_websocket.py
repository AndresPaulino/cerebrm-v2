import asyncio
import logging
from app.services.polygon_service import polygon_ws, run_polygon_websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_polygon_connection():
    try:
        # Initialize the WebSocket connection
        logger.info("Initializing WebSocket connection...")
        await polygon_ws.connect()

        # Subscribe to test symbols
        test_symbols = ["AAPL", "TSLA", "NVDA"]
        logger.info(f"Subscribing to symbols: {test_symbols}")
        await polygon_ws.subscribe(test_symbols)

        # Run the WebSocket for a short period
        logger.info(f"Listening for messages from {test_symbols}...")
        for _ in range(30):  # Listen for 30 seconds, logging every second
            await asyncio.sleep(1)
            logger.info("Waiting for messages...")

        # Unsubscribe from test symbols
        logger.info(f"Unsubscribing from symbols: {test_symbols}")
        await polygon_ws.unsubscribe(test_symbols)

        logger.info("Test complete.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_polygon_connection())