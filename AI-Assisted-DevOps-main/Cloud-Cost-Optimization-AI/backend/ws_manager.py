"""
WebSocket connection manager for real-time progress tracking during analyses.
"""
from typing import Set, Dict, List
import asyncio
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.message_history: Dict[str, List[str]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, analysis_id: str, websocket: WebSocket):
        """Register a WebSocket connection for an analysis."""
        await websocket.accept()
        async with self.lock:
            if analysis_id not in self.active_connections:
                self.active_connections[analysis_id] = []
            self.active_connections[analysis_id].append(websocket)
            history = list(self.message_history.get(analysis_id, []))
        for message in history:
            await websocket.send_text(message)

    async def disconnect(self, analysis_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        async with self.lock:
            if analysis_id in self.active_connections:
                self.active_connections[analysis_id].remove(websocket)
                if not self.active_connections[analysis_id]:
                    del self.active_connections[analysis_id]

    async def broadcast(self, analysis_id: str, message: str):
        """Send a message to all clients listening to an analysis."""
        async with self.lock:
            history = self.message_history.setdefault(analysis_id, [])
            history.append(message)
            del history[:-20]
            connections = self.active_connections.get(analysis_id, [])
        
        # Remove dead connections
        dead_connections = []
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        
        # Clean up dead connections
        if dead_connections:
            async with self.lock:
                for conn in dead_connections:
                    if analysis_id in self.active_connections and conn in self.active_connections[analysis_id]:
                        self.active_connections[analysis_id].remove(conn)


# Global connection manager
progress_manager = ConnectionManager()
