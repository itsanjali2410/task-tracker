from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    type: str
    related_task_id: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    action_type: str
    user_id: str
    user_name: str
    user_email: str
    task_id: Optional[str] = None
    metadata: Dict[str, Any]
    timestamp: datetime
