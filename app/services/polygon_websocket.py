from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage
from typing import List

client = WebSocketClient("FNk3clfL6XukuDn6qZKSQ48vWh4piQhh")

# subscribes to all trades
client.subscribe("A.*")

def handle_msg(msgs: List[WebSocketMessage]):
    for m in msgs:
        print(m)

client.run(handle_msg)