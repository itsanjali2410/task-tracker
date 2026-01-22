from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional

class NotificationInDB(BaseModel):
    """Notification model for MongoDB storage"""
    id: str
    user_id: str
    type: str  # task_assigned, task_overdue, comment_added, file_uploaded, status_changed
    related_task_id: Optional[str] = None
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
