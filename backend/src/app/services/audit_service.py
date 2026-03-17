import uuid
from datetime import datetime, timezone
from app.models.audit_log import AuditLogInDB
from app.db.mongodb import get_database
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def log_audit(
    action_type: str,
    user_id: str,
    user_name: str,
    user_email: str,
    task_id: Optional[str] = None,
    metadata: Dict[str, Any] = None
):
    """
    Create an audit log entry
    
    Args:
        action_type: Type of action (task_created, task_updated, etc.)
        user_id: ID of user performing action
        user_name: Name of user
        user_email: Email of user
        task_id: Related task ID (optional)
        metadata: Additional metadata (old_value, new_value, etc.)
    """
    try:
        db = get_database()
        
        audit_log = AuditLogInDB(
            id=str(uuid.uuid4()),
            action_type=action_type,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        audit_dict = audit_log.model_dump()
        audit_dict["timestamp"] = audit_dict["timestamp"].isoformat()
        
        await db.audit_logs.insert_one(audit_dict)
        logger.info(f"Audit log created: {action_type} by {user_email}")
        
        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        return None

async def get_audit_logs(
    limit: int = 100,
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None
):
    """
    Get audit logs with optional filters
    
    Args:
        limit: Maximum number of logs to return
        action_type: Filter by action type
        user_id: Filter by user
        task_id: Filter by task
    """
    try:
        db = get_database()
        
        query = {}
        if action_type:
            query["action_type"] = action_type
        if user_id:
            query["user_id"] = user_id
        if task_id:
            query["task_id"] = task_id
        
        logs = await db.audit_logs.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Convert datetime strings
        for log in logs:
            if isinstance(log.get('timestamp'), str):
                log['timestamp'] = datetime.fromisoformat(log['timestamp'])
        
        return logs
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        return []
