"""
WebSocket Connection Manager for real-time notifications and chat
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time features"""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # conversation_id -> set of user_ids currently typing
        self.typing_users: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept connection and add to active connections"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove connection from active connections"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user (all their connections)"""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
                    disconnected.add(websocket)
            # Clean up disconnected sockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
    
    async def send_to_users(self, user_ids: list, message: dict):
        """Send message to multiple users"""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)
    
    async def broadcast_notification(self, user_id: str, notification: dict):
        """Broadcast notification to user"""
        await self.send_to_user(user_id, {
            "type": "notification",
            "data": notification
        })
    
    async def broadcast_chat_message(self, participant_ids: list, message: dict):
        """Broadcast chat message to all participants"""
        await self.send_to_users(participant_ids, {
            "type": "chat_message",
            "data": message
        })
    
    async def broadcast_typing(self, conversation_id: str, user_id: str, user_name: str, participant_ids: list, is_typing: bool):
        """Broadcast typing indicator to conversation participants"""
        if is_typing:
            if conversation_id not in self.typing_users:
                self.typing_users[conversation_id] = set()
            self.typing_users[conversation_id].add(user_id)
        else:
            if conversation_id in self.typing_users:
                self.typing_users[conversation_id].discard(user_id)
        
        # Send to all participants except the typing user
        for pid in participant_ids:
            if pid != user_id:
                await self.send_to_user(pid, {
                    "type": "typing",
                    "data": {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "user_name": user_name,
                        "is_typing": is_typing
                    }
                })
    
    async def broadcast_read_receipt(self, conversation_id: str, user_id: str, message_ids: list, participant_ids: list):
        """Broadcast read receipt to conversation participants"""
        for pid in participant_ids:
            if pid != user_id:
                await self.send_to_user(pid, {
                    "type": "read_receipt",
                    "data": {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "message_ids": message_ids
                    }
                })
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user has active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global connection manager instance
manager = ConnectionManager()
