import asyncio
import websockets
import json

async def binance_websocket():
    # Binance WebSocket endpoint for BTC trades
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            trade_data = json.loads(message)
            print(f"Trade ID: {trade_data['t']}, Price: {trade_data['p']}, Quantity: {trade_data['q']}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(binance_websocket())

