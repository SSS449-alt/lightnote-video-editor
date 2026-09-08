"""
WebSocket connection manager for real-time pipeline progress streaming.
"""
from typing import Dict, Optional
from fastapi import WebSocket
import json
import asyncio


class WebSocketManager:
    """
    Manages active WebSocket connections per job.
    Allows the Celery worker to push progress updates to connected clients.
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[job_id] = websocket
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to job progress stream"
        })
    
    def disconnect(self, job_id: str):
        self.connections.pop(job_id, None)
    
    async def send_progress(self, job_id: str, data: dict):
        """Send progress update to connected client"""
        websocket = self.connections.get(job_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(job_id)
    
    async def broadcast_to_job(self, job_id: str, message_type: str, 
                                 stage: str, progress: int, message: str,
                                 extra: Optional[dict] = None):
        """Structured broadcast helper"""
        payload = {
            "type": message_type,
            "job_id": job_id,
            "stage": stage,
            "stage_progress": progress,
            "message": message,
        }
        if extra:
            payload.update(extra)
        
        await self.send_progress(job_id, payload)


# Singleton
websocket_manager = WebSocketManager()