"""
Chat API Routes - Direct Messages and Group Chats
With pinning and search features
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from typing import List, Optional
from app.schemas.chat import (
    ConversationCreate, ConversationResponse, ConversationUpdate,
    MessageCreate, MessageResponse, ChatAttachmentResponse,
    TypingIndicator, ReadReceipt, PinConversation, PinMessage, MessageSearchResponse
)
from app.models.chat import ConversationInDB, MessageInDB, ChatAttachmentInDB
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user
from app.services.websocket_manager import manager
import uuid
import os
import aiofiles
import re
from datetime import datetime, timezone

router = APIRouter(prefix="/chat", tags=["Chat"])

# Allowed file types for chat attachments
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "/app/backend/uploads/chat"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new conversation (DM or Group)
    - Everyone can create conversations
    - For DM: participant_ids should have 1 user ID
    - For Group: participant_ids should have 2+ user IDs, name is required
    """
    db = get_database()
    
    # Validate participants
    if not conv_data.participant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one participant is required"
        )
    
    # Add current user to participants
    all_participants = list(set(conv_data.participant_ids + [current_user.id]))
    
    if conv_data.is_group:
        if len(all_participants) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group chat requires at least 3 participants"
            )
        if not conv_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group name is required"
            )
    else:
        # For DM, check if conversation already exists
        if len(all_participants) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direct message must have exactly 2 participants"
            )
        
        existing_conv = await db.conversations.find_one({
            "is_group": False,
            "participants": {"$all": all_participants, "$size": 2}
        }, {"_id": 0})
        
        if existing_conv:
            # Return existing conversation
            if isinstance(existing_conv.get('created_at'), str):
                existing_conv['created_at'] = datetime.fromisoformat(existing_conv['created_at'])
            if isinstance(existing_conv.get('updated_at'), str):
                existing_conv['updated_at'] = datetime.fromisoformat(existing_conv['updated_at'])
            if isinstance(existing_conv.get('last_message_at'), str):
                existing_conv['last_message_at'] = datetime.fromisoformat(existing_conv['last_message_at'])
            return ConversationResponse(**existing_conv, unread_count=0)
    
    # Fetch participant names
    users = await db.users.find(
        {"id": {"$in": all_participants}},
        {"_id": 0, "id": 1, "full_name": 1}
    ).to_list(100)
    
    user_names = {u["id"]: u["full_name"] for u in users}
    participant_names = [user_names.get(pid, "Unknown") for pid in all_participants]
    
    # Create conversation
    conversation = ConversationInDB(
        id=str(uuid.uuid4()),
        name=conv_data.name,
        is_group=conv_data.is_group,
        participants=all_participants,
        participant_names=participant_names,
        created_by=current_user.id
    )
    
    conv_dict = conversation.model_dump()
    conv_dict["created_at"] = conv_dict["created_at"].isoformat()
    conv_dict["updated_at"] = conv_dict["updated_at"].isoformat()
    
    await db.conversations.insert_one(conv_dict)
    
    return ConversationResponse(
        **conversation.model_dump(),
        unread_count=0
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: UserResponse = Depends(get_current_user)
):
    """List all conversations for current user"""
    db = get_database()
    
    conversations = await db.conversations.find(
        {"participants": current_user.id},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    
    result = []
    for conv in conversations:
        # Convert datetime strings
        if isinstance(conv.get('created_at'), str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv.get('updated_at'), str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
        if isinstance(conv.get('last_message_at'), str):
            conv['last_message_at'] = datetime.fromisoformat(conv['last_message_at'])
        
        # Count unread messages
        unread_count = await db.messages.count_documents({
            "conversation_id": conv["id"],
            "sender_id": {"$ne": current_user.id},
            "read_by": {"$nin": [current_user.id]}
        })
        
        # Check if current user has pinned this conversation
        is_pinned = current_user.id in conv.get("pinned_by", [])
        
        result.append(ConversationResponse(**conv, unread_count=unread_count, is_pinned=is_pinned))
    
    # Sort: pinned first, then by updated_at
    result.sort(key=lambda x: (not x.is_pinned, x.updated_at), reverse=True)
    
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get conversation by ID"""
    db = get_database()
    
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Convert datetime strings
    if isinstance(conv.get('created_at'), str):
        conv['created_at'] = datetime.fromisoformat(conv['created_at'])
    if isinstance(conv.get('updated_at'), str):
        conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
    if isinstance(conv.get('last_message_at'), str):
        conv['last_message_at'] = datetime.fromisoformat(conv['last_message_at'])
    
    # Count unread messages
    unread_count = await db.messages.count_documents({
        "conversation_id": conversation_id,
        "sender_id": {"$ne": current_user.id},
        "read_by": {"$nin": [current_user.id]}
    })
    
    return ConversationResponse(**conv, unread_count=unread_count)


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update conversation (groups only) - add/remove participants, change name"""
    db = get_database()
    
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if not conv.get("is_group"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update direct message conversations"
        )
    
    updates = {}
    
    if update_data.name:
        updates["name"] = update_data.name
    
    new_participants = conv["participants"]
    new_names = conv.get("participant_names", [])
    
    if update_data.add_participants:
        # Fetch new participant names
        new_users = await db.users.find(
            {"id": {"$in": update_data.add_participants}},
            {"_id": 0, "id": 1, "full_name": 1}
        ).to_list(100)
        
        for user in new_users:
            if user["id"] not in new_participants:
                new_participants.append(user["id"])
                new_names.append(user["full_name"])
    
    if update_data.remove_participants:
        # Don't allow removing all participants or the creator
        for pid in update_data.remove_participants:
            if pid != conv["created_by"] and pid in new_participants:
                idx = new_participants.index(pid)
                new_participants.pop(idx)
                if idx < len(new_names):
                    new_names.pop(idx)
    
    if len(new_participants) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group must have at least 2 participants"
        )
    
    updates["participants"] = new_participants
    updates["participant_names"] = new_names
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": updates}
    )
    
    # Fetch updated conversation
    updated_conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if isinstance(updated_conv.get('created_at'), str):
        updated_conv['created_at'] = datetime.fromisoformat(updated_conv['created_at'])
    if isinstance(updated_conv.get('updated_at'), str):
        updated_conv['updated_at'] = datetime.fromisoformat(updated_conv['updated_at'])
    if isinstance(updated_conv.get('last_message_at'), str):
        updated_conv['last_message_at'] = datetime.fromisoformat(updated_conv['last_message_at'])
    
    return ConversationResponse(**updated_conv, unread_count=0)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send a message to a conversation"""
    db = get_database()
    
    # Verify conversation exists and user is participant
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # If attachment message, verify attachment exists
    attachment_name = None
    attachment_type = None
    if message_data.message_type == "attachment" and message_data.attachment_id:
        attachment = await db.chat_attachments.find_one(
            {"id": message_data.attachment_id},
            {"_id": 0}
        )
        if attachment:
            attachment_name = attachment.get("file_name")
            attachment_type = attachment.get("file_type")
    
    # Create message
    message = MessageInDB(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        content=message_data.content,
        message_type=message_data.message_type,
        attachment_id=message_data.attachment_id,
        attachment_name=attachment_name,
        attachment_type=attachment_type,
        read_by=[current_user.id]  # Sender has read it
    )
    
    msg_dict = message.model_dump()
    msg_dict["created_at"] = msg_dict["created_at"].isoformat()
    
    await db.messages.insert_one(msg_dict)
    
    # Update conversation last message
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "last_message": message_data.content[:100],
            "last_message_at": msg_dict["created_at"],
            "updated_at": msg_dict["created_at"]
        }}
    )
    
    # Broadcast message via WebSocket to all participants
    await manager.broadcast_chat_message(
        conv["participants"],
        {
            "id": message.id,
            "conversation_id": conversation_id,
            "sender_id": current_user.id,
            "sender_name": current_user.full_name,
            "content": message_data.content,
            "message_type": message_data.message_type,
            "attachment_id": message_data.attachment_id,
            "attachment_name": attachment_name,
            "attachment_type": attachment_type,
            "read_by": [current_user.id],
            "created_at": msg_dict["created_at"]
        }
    )
    
    return MessageResponse(
        **message.model_dump(),
        is_own=True
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get messages from a conversation"""
    db = get_database()
    
    # Verify conversation exists and user is participant
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    query = {"conversation_id": conversation_id}
    if before:
        # Get message timestamp for pagination
        before_msg = await db.messages.find_one({"id": before}, {"_id": 0, "created_at": 1})
        if before_msg:
            query["created_at"] = {"$lt": before_msg["created_at"]}
    
    messages = await db.messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Reverse to get chronological order
    messages.reverse()
    
    result = []
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
        
        result.append(MessageResponse(
            **msg,
            is_own=msg["sender_id"] == current_user.id
        ))
    
    return result


@router.post("/conversations/{conversation_id}/read")
async def mark_messages_read(
    conversation_id: str,
    read_data: ReadReceipt,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark messages as read"""
    db = get_database()
    
    # Verify conversation
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Update messages
    await db.messages.update_many(
        {
            "id": {"$in": read_data.message_ids},
            "conversation_id": conversation_id
        },
        {"$addToSet": {"read_by": current_user.id}}
    )
    
    # Broadcast read receipt via WebSocket
    await manager.broadcast_read_receipt(
        conversation_id,
        current_user.id,
        read_data.message_ids,
        conv["participants"]
    )
    
    return {"message": "Messages marked as read"}


@router.post("/conversations/{conversation_id}/typing")
async def typing_indicator(
    conversation_id: str,
    typing_data: TypingIndicator,
    current_user: UserResponse = Depends(get_current_user)
):
    """Send typing indicator"""
    db = get_database()
    
    # Verify conversation
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Broadcast typing indicator
    await manager.broadcast_typing(
        conversation_id,
        current_user.id,
        current_user.full_name,
        conv["participants"],
        typing_data.is_typing
    )
    
    return {"message": "Typing indicator sent"}


@router.post("/conversations/{conversation_id}/attachments", response_model=ChatAttachmentResponse)
async def upload_chat_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload attachment for chat"""
    db = get_database()
    
    # Verify conversation
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Validate file
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )
    
    # Generate unique filename
    attachment_id = str(uuid.uuid4())
    safe_filename = f"{attachment_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Create attachment record
    attachment = ChatAttachmentInDB(
        id=attachment_id,
        conversation_id=conversation_id,
        message_id="",  # Will be set when message is sent
        uploaded_by=current_user.id,
        uploaded_by_name=current_user.full_name,
        file_name=file.filename,
        file_type=file_ext,
        file_size=len(content),
        file_path=file_path
    )
    
    att_dict = attachment.model_dump()
    att_dict["uploaded_at"] = att_dict["uploaded_at"].isoformat()
    
    await db.chat_attachments.insert_one(att_dict)
    
    return ChatAttachmentResponse(**attachment.model_dump())


@router.get("/attachments/{attachment_id}/download")
async def download_chat_attachment(
    attachment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Download chat attachment"""
    from fastapi.responses import FileResponse
    
    db = get_database()
    
    attachment = await db.chat_attachments.find_one(
        {"id": attachment_id},
        {"_id": 0}
    )
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Verify user is participant of conversation
    conv = await db.conversations.find_one(
        {"id": attachment["conversation_id"], "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attachment"
        )
    
    if not os.path.exists(attachment["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        attachment["file_path"],
        filename=attachment["file_name"],
        media_type="application/octet-stream"
    )


@router.get("/users/available", response_model=List[dict])
async def get_available_users_for_chat(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get list of users available for chat (excluding current user)"""
    db = get_database()
    
    users = await db.users.find(
        {"id": {"$ne": current_user.id}, "is_active": True},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "role": 1}
    ).to_list(100)
    
    return users


# ============================================
# PIN AND SEARCH ENDPOINTS
# ============================================

@router.post("/conversations/{conversation_id}/pin")
async def pin_conversation(
    conversation_id: str,
    pin_data: PinConversation,
    current_user: UserResponse = Depends(get_current_user)
):
    """Pin or unpin a conversation for the current user"""
    db = get_database()
    
    # Verify conversation exists and user is participant
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if pin_data.pin:
        # Pin: add user to pinned_by list
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$addToSet": {"pinned_by": current_user.id}}
        )
        return {"message": "Conversation pinned", "is_pinned": True}
    else:
        # Unpin: remove user from pinned_by list
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$pull": {"pinned_by": current_user.id}}
        )
        return {"message": "Conversation unpinned", "is_pinned": False}


@router.post("/conversations/{conversation_id}/messages/{message_id}/pin")
async def pin_message(
    conversation_id: str,
    message_id: str,
    pin_data: PinMessage,
    current_user: UserResponse = Depends(get_current_user)
):
    """Pin or unpin a message in a conversation"""
    db = get_database()
    
    # Verify conversation exists and user is participant
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Verify message exists
    message = await db.messages.find_one(
        {"id": message_id, "conversation_id": conversation_id},
        {"_id": 0}
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    if pin_data.pin:
        # Pin message
        await db.messages.update_one(
            {"id": message_id},
            {"$set": {
                "is_pinned": True,
                "pinned_by": current_user.id,
                "pinned_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Message pinned", "is_pinned": True}
    else:
        # Unpin message
        await db.messages.update_one(
            {"id": message_id},
            {"$set": {
                "is_pinned": False,
                "pinned_by": None,
                "pinned_at": None
            }}
        )
        return {"message": "Message unpinned", "is_pinned": False}


@router.get("/conversations/{conversation_id}/pinned-messages", response_model=List[MessageResponse])
async def get_pinned_messages(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all pinned messages in a conversation"""
    db = get_database()
    
    # Verify conversation
    conv = await db.conversations.find_one(
        {"id": conversation_id, "participants": current_user.id},
        {"_id": 0}
    )
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id, "is_pinned": True},
        {"_id": 0}
    ).sort("pinned_at", -1).to_list(100)
    
    result = []
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
        if isinstance(msg.get('pinned_at'), str):
            msg['pinned_at'] = datetime.fromisoformat(msg['pinned_at'])
        
        result.append(MessageResponse(
            **msg,
            is_own=msg["sender_id"] == current_user.id
        ))
    
    return result


@router.get("/search", response_model=List[MessageSearchResponse])
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Search messages across all conversations or within a specific conversation
    - Searches in message content
    - Only returns messages from conversations user participates in
    """
    db = get_database()
    
    # Get all conversations user participates in
    user_convs = await db.conversations.find(
        {"participants": current_user.id},
        {"_id": 0, "id": 1, "name": 1, "is_group": 1, "participant_names": 1, "participants": 1}
    ).to_list(100)
    
    conv_ids = [c["id"] for c in user_convs]
    conv_map = {c["id"]: c for c in user_convs}
    
    if not conv_ids:
        return []
    
    # Build search query
    query = {
        "conversation_id": {"$in": conv_ids},
        "content": {"$regex": re.escape(q), "$options": "i"}
    }
    
    if conversation_id:
        if conversation_id not in conv_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        query["conversation_id"] = conversation_id
    
    messages = await db.messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    result = []
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
        
        conv = conv_map.get(msg["conversation_id"], {})
        
        # Get conversation name
        if conv.get("is_group"):
            conv_name = conv.get("name", "Group")
        else:
            # For DM, get the other participant's name
            other_idx = next((i for i, pid in enumerate(conv.get("participants", [])) if pid != current_user.id), 0)
            conv_name = conv.get("participant_names", ["Unknown"])[other_idx] if other_idx < len(conv.get("participant_names", [])) else "Unknown"
        
        result.append(MessageSearchResponse(
            id=msg["id"],
            conversation_id=msg["conversation_id"],
            conversation_name=conv_name,
            sender_id=msg["sender_id"],
            sender_name=msg["sender_name"],
            content=msg["content"],
            created_at=msg["created_at"],
            is_pinned=msg.get("is_pinned", False)
        ))
    
    return result
