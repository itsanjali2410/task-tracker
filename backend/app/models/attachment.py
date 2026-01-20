from datetime import datetime, timezone
from pydantic import BaseModel, Field

class AttachmentInDB(BaseModel):
    """Attachment model for MongoDB storage"""
    id: str
    task_id: str
    uploaded_by: str  # User ID
    uploaded_by_name: str
    uploaded_by_email: str
    file_name: str
    file_type: str  # pdf, jpg, png, doc, docx
    file_size: int  # in bytes
    file_path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
