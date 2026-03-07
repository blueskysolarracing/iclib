import asyncio
import websockets

async def send_hello(websocket):
    print("External computer connected!")
    try:
        while True:
            # Send the simple string message
            for i in range(100):
                await websocket.send(str(i))
            
                # Pause for 2 seconds before sending again
                await asyncio.sleep(2) 
            
    except websockets.exceptions.ConnectionClosed:
        print("Connection lost. Waiting for reconnect...")

async def main():
    # 0.0.0.0 allows connections from any IP on the network
    async with websockets.serve(send_hello, "0.0.0.0", 8765):
        print("WebSocket Server running on port 8765...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())