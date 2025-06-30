import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from utils.singleton import singleton


@singleton
class ConnectionManager:
    def __init__(self):
        # Store active WebSocket connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection and adds it to the list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"New connection accepted: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection from the list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Connection closed: {websocket.client}")

    async def send_personal_message(self, message: Any, websocket: WebSocket):
        """Sends a message (text or json) to a specific WebSocket."""
        try:
            if isinstance(message, str):
                await websocket.send_text(message)
            else:  # Assume JSON serializable dict/list etc.
                await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message to {websocket.client}: {e}")

    async def broadcast(self, message: Any):
        """Sends a message (text or json) to all active connections."""
        # Create tasks for sending messages concurrently
        tasks = []
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                if isinstance(message, str):
                    tasks.append(connection.send_text(message))
                else:
                    with open('socket.log', 'a') as f:
                        import json
                        f.write(json.dumps(message)+'\n')
                    tasks.append(connection.send_json(message))
            except Exception as e:
                # Handle immediate error (less likely here, more likely during await gather)
                print(f"Error preparing broadcast for {connection.client}: {e}")
                disconnected_clients.append(connection)  # Mark for removal

        # Execute all send tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results for exceptions (indicating failed sends/disconnects)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                connection = self.active_connections[i]  # Find corresponding connection
                print(f"Error broadcasting to {connection.client}: {result}")
                disconnected_clients.append(connection)

        # Remove clients that failed or disconnected during broadcast
        for client in set(disconnected_clients):  # Use set to avoid duplicates
            self.disconnect(client)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    Handles the entire lifecycle for a single WebSocket connection.
    Equivalent to connect, disconnect, and message handlers combined.
    """
    await manager.connect(websocket)
    try:
        # Loop indefinitely, waiting for messages from the client
        while True:
            data = await websocket.receive_json()

            print(f"Message received from {websocket.client}: {data}")

            # TODO: remove in future, right now FE is not sending anything
            response_data = {"status": "received", "original_data": data}
            await manager.send_personal_message(response_data, websocket)

    except WebSocketDisconnect:
        print(f"WebSocketDisconnect detected for {websocket.client}")

    except Exception as e:
        print(f"Error in WebSocket connection {websocket.client}: {e}")
    finally:
        manager.disconnect(websocket)
