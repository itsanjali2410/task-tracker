from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.schemas.notification import AuditLogResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user, require_role
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    task_id: Optional[str] = Query(None, description="Filter by task"),
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Get audit logs (Admin and Manager only)
    - Returns logs sorted by newest first
    - Supports filtering by action_type, user_id, and task_id
    """
    logs = await get_audit_logs(
        limit=limit,
        action_type=action_type,
        user_id=user_id,
        task_id=task_id
    )
    
    return [AuditLogResponse(**log) for log in logs]
