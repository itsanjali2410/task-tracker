from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.models.comment import CommentInDB
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit
from app.services.email_service import send_comment_notification_email
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a comment on a task
    - Any authenticated user can comment
    - Comments are linked to task and user
    """
    db = get_database()
    
    # Verify task exists
    task = await db.tasks.find_one({"id": comment_data.task_id}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check authorization for team members
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to comment on this task"
        )
    
    # Create comment document
    comment_in_db = CommentInDB(
        id=str(uuid.uuid4()),
        task_id=comment_data.task_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        content=comment_data.content
    )
    
    # Convert to dict and serialize datetime
    comment_dict = comment_in_db.model_dump()
    comment_dict["created_at"] = comment_dict["created_at"].isoformat()
    comment_dict["updated_at"] = comment_dict["updated_at"].isoformat()
    
    await db.comments.insert_one(comment_dict)
    
    # Notify task participants (assigned user and creator)
    participants = set([task["assigned_to"], task["created_by"]])
    participants.discard(current_user.id)  # Don't notify the commenter
    
    for participant_id in participants:
        await create_notification(
            user_id=participant_id,
            notification_type="comment_added",
            message=f"{current_user.full_name} commented on task: '{task['title']}'",
            related_task_id=comment_data.task_id
        )
        
        # Send email notification
        user = await db.users.find_one({"id": participant_id}, {"_id": 0})
        if user:
            send_comment_notification_email(
                to_email=user["email"],
                to_name=user["full_name"],
                task_title=task["title"],
                commenter_name=current_user.full_name,
                comment_preview=comment_data.content
            )
    
    # Log audit
    await log_audit(
        action_type="comment_added",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=comment_data.task_id,
        metadata={
            "task_title": task["title"],
            "comment_length": len(comment_data.content)
        }
    )
    
    return CommentResponse(**comment_in_db.model_dump())

@router.get("/task/{task_id}", response_model=List[CommentResponse])
async def list_comments_by_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all comments for a specific task
    - Ordered by creation date (oldest first)
    - All authenticated users can view comments (since all tasks are visible)
    """
    db = get_database()
    
    # Verify task exists
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Fetch comments
    comments = await db.comments.find(
        {"task_id": task_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    # Convert datetime strings
    for comment in comments:
        if isinstance(comment.get('created_at'), str):
            comment['created_at'] = datetime.fromisoformat(comment['created_at'])
        if isinstance(comment.get('updated_at'), str):
            comment['updated_at'] = datetime.fromisoformat(comment['updated_at'])
    
    return [CommentResponse(**comment) for comment in comments]

@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific comment by ID
    """
    db = get_database()
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Convert datetime strings
    if isinstance(comment.get('created_at'), str):
        comment['created_at'] = datetime.fromisoformat(comment['created_at'])
    if isinstance(comment.get('updated_at'), str):
        comment['updated_at'] = datetime.fromisoformat(comment['updated_at'])
    
    return CommentResponse(**comment)

@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update a comment
    - Only the comment author can update their comment
    """
    db = get_database()
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only comment author can update
    if comment["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    update_data = {
        "content": comment_update.content,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.comments.update_one({"id": comment_id}, {"$set": update_data})
    
    # Fetch updated comment
    updated_comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    
    # Convert datetime strings
    if isinstance(updated_comment.get('created_at'), str):
        updated_comment['created_at'] = datetime.fromisoformat(updated_comment['created_at'])
    if isinstance(updated_comment.get('updated_at'), str):
        updated_comment['updated_at'] = datetime.fromisoformat(updated_comment['updated_at'])
    
    return CommentResponse(**updated_comment)

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a comment
    - Only the comment author or admin can delete
    """
    db = get_database()
    comment = await db.comments.find_one({"id": comment_id}, {"_id": 0})
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only comment author or admin can delete
    if comment["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    result = await db.comments.delete_one({"id": comment_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    return None
