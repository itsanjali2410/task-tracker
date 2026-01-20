from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AttachmentUpload(BaseModel):
    task_id: str

class AttachmentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    task_id: str
    uploaded_by: str
    uploaded_by_name: str
    uploaded_by_email: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    uploaded_at: datetime

class UserProductivity(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    total_tasks_assigned: int
    tasks_completed: int
    tasks_completed_on_time: int
    overdue_tasks: int
    average_completion_time_hours: float
    productivity_score: float  # 0-100

class TeamOverview(BaseModel):
    total_users: int
    total_tasks: int
    total_completed: int
    total_overdue: int
    average_productivity_score: float
    user_stats: list[UserProductivity]
