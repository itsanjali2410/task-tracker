from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AuditLogInDB(BaseModel):
    """Audit log model for MongoDB storage"""
    id: str
    action_type: str  # task_created, task_updated, status_changed, file_uploaded, comment_added, user_created
    user_id: str
    user_name: str
    user_email: str
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # old_value, new_value, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
