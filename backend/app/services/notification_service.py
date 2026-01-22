import uuid
from datetime import datetime, timezone
from app.models.notification import NotificationInDB
from app.db.mongodb import get_database
import logging

logger = logging.getLogger(__name__)

async def create_notification(
    user_id: str,
    notification_type: str,
    message: str,
    related_task_id: str = None
):
    """
    Create a notification for a user
    
    Args:
        user_id: ID of user to notify
        notification_type: Type of notification (task_assigned, task_overdue, etc.)
        message: Notification message
        related_task_id: Related task ID (optional)
    """
    try:
        db = get_database()
        
        notification = NotificationInDB(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=notification_type,
            related_task_id=related_task_id,
            message=message,
            is_read=False
        )
        
        notification_dict = notification.model_dump()
        notification_dict["created_at"] = notification_dict["created_at"].isoformat()
        
        await db.notifications.insert_one(notification_dict)
        logger.info(f"Notification created for user {user_id}: {notification_type}")
        
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None

async def get_user_notifications(user_id: str, unread_only: bool = False, limit: int = 50):
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        unread_only: Return only unread notifications
        limit: Maximum number of notifications to return
    """
    try:
        db = get_database()
        
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        notifications = await db.notifications.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Convert datetime strings
        for notification in notifications:
            if isinstance(notification.get('created_at'), str):
                notification['created_at'] = datetime.fromisoformat(notification['created_at'])
        
        return notifications
    except Exception as e:
        logger.error(f"Failed to get notifications: {str(e)}")
        return []

async def mark_notification_read(notification_id: str, user_id: str):
    """
    Mark a notification as read
    
    Args:
        notification_id: Notification ID
        user_id: User ID (for authorization)
    """
    try:
        db = get_database()
        
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": user_id},
            {"$set": {"is_read": True}}
        )
        
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {str(e)}")
        return False

async def mark_all_notifications_read(user_id: str):
    """
    Mark all notifications as read for a user
    
    Args:
        user_id: User ID
    """
    try:
        db = get_database()
        
        result = await db.notifications.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        
        return result.modified_count
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {str(e)}")
        return 0
