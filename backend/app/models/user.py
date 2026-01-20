from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserInDB(BaseModel):
    """User model for MongoDB storage"""
    id: str
    email: EmailStr
    full_name: str
    hashed_password: str
    role: str  # 'admin', 'manager', 'team_member'
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
