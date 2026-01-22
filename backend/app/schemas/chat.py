"""
Chat Schemas for API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Conversation schemas
class ConversationCreate(BaseModel):
    """Create conversation request"""
    name: Optional[str] = None  # Required for groups
    is_group: bool = False
    participant_ids: List[str]  # For DM: single user ID, For group: multiple user IDs

class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    name: Optional[str] = None
    is_group: bool
    participants: List[str]
    participant_names: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_pinned: bool = False  # Whether current user has pinned this

class ConversationUpdate(BaseModel):
    """Update conversation (groups only)"""
    name: Optional[str] = None
    add_participants: Optional[List[str]] = None
    remove_participants: Optional[List[str]] = None

# Message schemas
class MessageCreate(BaseModel):
    """Create message request"""
    content: str
    message_type: str = "text"  # text or attachment
    attachment_id: Optional[str] = None

class MessageResponse(BaseModel):
    """Message response"""
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    content: str
    message_type: str
    attachment_id: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    read_by: List[str]
    created_at: datetime
    is_own: bool = False  # Set by API based on current user
    is_pinned: bool = False
    pinned_by: Optional[str] = None
    pinned_at: Optional[datetime] = None

class ChatAttachmentResponse(BaseModel):
    """Chat attachment response"""
    id: str
    conversation_id: str
    message_id: str
    uploaded_by: str
    uploaded_by_name: str
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: datetime

# Typing indicator
class TypingIndicator(BaseModel):
    """Typing indicator request"""
    conversation_id: str
    is_typing: bool

# Read receipt
class ReadReceipt(BaseModel):
    """Mark messages as read request"""
    message_ids: List[str]

# Pin schemas
class PinConversation(BaseModel):
    """Pin/unpin conversation request"""
    pin: bool = True

class PinMessage(BaseModel):
    """Pin/unpin message request"""
    pin: bool = True

# Search schema
class MessageSearchResponse(BaseModel):
    """Search result response"""
    id: str
    conversation_id: str
    conversation_name: Optional[str]
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime
    is_pinned: bool = False
