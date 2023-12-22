import asyncio
import websockets
import json

async def subscribe_to_bitcoin_transactions():
    uri = "wss://ws.yobp0j.tech.openmesh.network"
    async with websockets.connect(uri) as websocket:
        # Constructing the subscription message
        subscribe_message = json.dumps({
            "action": "subscribe",
            "channel": "trades",
            "exchange": "coinbase",
            "symbol": "BTC.USD"
        })
        await websocket.send(subscribe_message)
        print(f"Subscribed to Bitcoin transactions on Coinbase: {subscribe_message}")

        # Receiving messages
        async for message in websocket:
            print("Received message:", message)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(subscribe_to_bitcoin_transactions())
