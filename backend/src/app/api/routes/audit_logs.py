from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.schemas.notification import AuditLogResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user, require_role
from app.services.audit_service import get_audit_logs
from app.core.roles import MANAGER_ROLES, NON_ADMIN_ROLES
from app.db.mongodb import get_database

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    task_id: Optional[str] = Query(None, description="Filter by task"),
    current_user: UserResponse = Depends(require_role(MANAGER_ROLES))
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


@router.get("/task/{task_id}", response_model=List[AuditLogResponse])
async def get_task_audit_logs(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get audit logs for a specific task
    - All authenticated users can view logs for tasks they created
    - Admins and Managers can view logs for any task
    """
    db = get_database()
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Authorization: allow if user is task creator, admin, or manager
    if current_user.role in NON_ADMIN_ROLES and task.get("created_by") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task's audit logs"
        )

    logs = await get_audit_logs(task_id=task_id, limit=500)
    return [AuditLogResponse(**log) for log in logs]
