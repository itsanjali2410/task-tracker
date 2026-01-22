from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from app.schemas.notification import NotificationResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user
from app.services.notification_service import (
    get_user_notifications,
    mark_notification_read,
    mark_all_notifications_read
)
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get notifications for current user
    - Returns notifications sorted by newest first
    - Can filter by unread only
    """
    notifications = await get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    
    return [NotificationResponse(**notif) for notif in notifications]

@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get count of unread notifications for current user
    """
    notifications = await get_user_notifications(
        user_id=current_user.id,
        unread_only=True,
        limit=1000
    )
    
    return {"unread_count": len(notifications)}

@router.post("/mark-read/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark a specific notification as read
    """
    success = await mark_notification_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read"
        )
    
    return None

@router.post("/mark-all-read", response_model=dict)
async def mark_all_as_read(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark all notifications as read for current user
    """
    count = await mark_all_notifications_read(current_user.id)
    
    return {"marked_read_count": count}
