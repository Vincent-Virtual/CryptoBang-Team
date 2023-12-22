import asyncio
import websockets

async def send_and_receive_message():
    uri = "wss://echo.websocket.org"
    
    async with websockets.connect(uri) as websocket:
        message = "Hello, WebSocket!"
        
        # Send the message
        await websocket.send(message)
        print(f"Sent: {message}")
        
        # Receive the echoed message
        response = await websocket.recv()
        print(f"Received: {response}")

if __name__ == "__main__":
    asyncio.run(send_and_receive_message())
