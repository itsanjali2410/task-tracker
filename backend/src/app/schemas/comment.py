from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    task_id: str

class CommentUpdate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    task_id: str
    user_id: str
    user_name: str
    user_email: str
    content: str
    created_at: datetime
    updated_at: datetime
