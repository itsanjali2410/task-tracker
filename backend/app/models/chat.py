"""
Chat Models for MongoDB
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

class ConversationInDB(BaseModel):
    """Conversation/Chat model"""
    id: str
    name: Optional[str] = None  # For group chats
    is_group: bool = False
    participants: List[str]  # List of user IDs
    participant_names: List[str] = []  # List of user names
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

class MessageInDB(BaseModel):
    """Chat Message model"""
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    content: str
    message_type: str = "text"  # text, attachment
    attachment_id: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    read_by: List[str] = []  # List of user IDs who have read this message
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatAttachmentInDB(BaseModel):
    """Chat Attachment model"""
    id: str
    conversation_id: str
    message_id: str
    uploaded_by: str
    uploaded_by_name: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
