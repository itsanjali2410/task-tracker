from datetime import datetime, timezone
from pydantic import BaseModel, Field

class CommentInDB(BaseModel):
    """Comment model for MongoDB storage"""
    id: str
    task_id: str  # Task ID
    user_id: str  # User ID who created the comment
    user_name: str
    user_email: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
