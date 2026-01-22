"""
WebSocket API Routes for real-time features
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import manager
from app.core.security import decode_access_token
from app.db.mongodb import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications and chat
    Connect with: ws://host/api/ws?token=<access_token>
    
    Message types received:
    - notification: New notification
    - chat_message: New chat message
    - typing: Typing indicator
    - read_receipt: Message read receipt
    """
    user_id = None
    
    try:
        # Verify token
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Verify user exists and is active
        db = get_database()
        user = await db.users.find_one({"id": user_id, "is_active": True}, {"_id": 0})
        if not user:
            await websocket.close(code=4001, reason="User not found or inactive")
            return
        
        # Connect
        await manager.connect(websocket, user_id)
        
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "data": {"user_id": user_id, "message": "WebSocket connected"}
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping/pong for keep-alive
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle typing indicator from client
                elif data.get("type") == "typing":
                    conversation_id = data.get("conversation_id")
                    is_typing = data.get("is_typing", False)
                    
                    if conversation_id:
                        # Get conversation participants
                        conv = await db.conversations.find_one(
                            {"id": conversation_id, "participants": user_id},
                            {"_id": 0, "participants": 1}
                        )
                        if conv:
                            await manager.broadcast_typing(
                                conversation_id,
                                user_id,
                                user.get("full_name", "Unknown"),
                                conv["participants"],
                                is_typing
                            )
                
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user_id:
            manager.disconnect(websocket, user_id)
