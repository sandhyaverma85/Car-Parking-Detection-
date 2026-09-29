"""
WebSocket Connection Manager — Phase 10

Manages connected dashboard clients and broadcasts live events.
Only authenticated connections receive violation data.
"""

from __future__ import annotations

import json
from typing import Dict, List, Set

from fastapi import WebSocket
from app.utils.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Two channels:
      - "occupancy": public occupancy updates (sent to all connected clients)
      - "violations": officer/admin only (role enforced at connection time)
    """

    def __init__(self) -> None:
        # channel → list of connected websockets
        self._channels: Dict[str, List[WebSocket]] = {
            "occupancy": [],
            "violations": [],
        }

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        if channel not in self._channels:
            self._channels[channel] = []
        self._channels[channel].append(websocket)
        log.info("ws_connected", channel=channel, total=len(self._channels[channel]))

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if channel in self._channels:
            try:
                self._channels[channel].remove(websocket)
            except ValueError:
                pass
        log.info("ws_disconnected", channel=channel)

    async def broadcast(self, channel: str, message: dict) -> None:
        """Broadcast a JSON message to all clients on a channel."""
        dead: List[WebSocket] = []
        for ws in list(self._channels.get(channel, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)

    async def broadcast_occupancy(
        self,
        camera_id: str,
        occupied: int,
        available: int,
        total: int,
        percentage: float,
    ) -> None:
        await self.broadcast("occupancy", {
            "type": "occupancy_update",
            "camera_id": camera_id,
            "occupied": occupied,
            "available": available,
            "total": total,
            "occupancy_percentage": percentage,
        })

    async def broadcast_violation(self, violation_data: dict) -> None:
        await self.broadcast("violations", {
            "type": "violation_alert",
            **violation_data,
        })


# Singleton instance used across the application
manager = ConnectionManager()
