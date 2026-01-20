from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class TaskInDB(BaseModel):
    """Task model for MongoDB storage"""
    id: str
    title: str
    description: str
    priority: str  # 'low', 'medium', 'high'
    status: str  # 'todo', 'in_progress', 'completed'
    assigned_to: str  # User ID
    assigned_to_email: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_by: str  # User ID
    created_by_name: Optional[str] = None
    due_date: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
