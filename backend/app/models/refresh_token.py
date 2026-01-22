from datetime import datetime, timezone
from pydantic import BaseModel, Field

class RefreshTokenInDB(BaseModel):
    """Refresh token model for MongoDB storage"""
    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_revoked: bool = False
