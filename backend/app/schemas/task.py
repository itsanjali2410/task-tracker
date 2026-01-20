from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: str
    priority: str
    due_date: str

class TaskCreate(TaskBase):
    assigned_to: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    description: str
    priority: str
    status: str
    assigned_to: str
    assigned_to_email: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    due_date: str
    created_at: datetime
    updated_at: datetime
