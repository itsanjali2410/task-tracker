from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.models.task import TaskInDB
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user, require_role
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit
from app.services.email_service import send_task_assigned_email
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Create a new task (Admin and Manager only)
    - Validates assigned user exists
    - Creates task in MongoDB
    """
    db = get_database()
    
    # Validate assigned user
    assigned_user = await db.users.find_one({"id": task_data.assigned_to}, {"_id": 0})
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found"
        )
    
    # Validate priority
    valid_priorities = ["low", "medium", "high"]
    if task_data.priority not in valid_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )
    
    # Create task document
    task_in_db = TaskInDB(
        id=str(uuid.uuid4()),
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status="todo",
        assigned_to=task_data.assigned_to,
        assigned_to_email=assigned_user["email"],
        assigned_to_name=assigned_user["full_name"],
        created_by=current_user.id,
        created_by_name=current_user.full_name,
        due_date=task_data.due_date
    )
    
    # Convert to dict and serialize datetime
    task_dict = task_in_db.model_dump()
    task_dict["created_at"] = task_dict["created_at"].isoformat()
    task_dict["updated_at"] = task_dict["updated_at"].isoformat()
    
    await db.tasks.insert_one(task_dict)
    
    # Create notification for assigned user
    await create_notification(
        user_id=task_data.assigned_to,
        notification_type="task_assigned",
        message=f"You have been assigned a new task: '{task_dict['title']}'",
        related_task_id=task_in_db.id
    )
    
    # Send email notification
    send_task_assigned_email(
        to_email=assigned_user["email"],
        to_name=assigned_user["full_name"],
        task_title=task_dict["title"],
        task_due_date=task_dict["due_date"],
        assigned_by=current_user.full_name
    )
    
    # Log audit
    await log_audit(
        action_type="task_created",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=task_in_db.id,
        metadata={
            "task_title": task_dict["title"],
            "assigned_to": assigned_user["full_name"],
            "priority": task_dict["priority"]
        }
    )
    
    return TaskResponse(**task_in_db.model_dump())

@router.get("", response_model=List[TaskResponse])
async def list_tasks(current_user: UserResponse = Depends(get_current_user)):
    """
    List tasks based on user role
    - Team members see only their assigned tasks
    - Admins and Managers see all tasks
    """
    db = get_database()
    
    if current_user.role == "team_member":
        tasks = await db.tasks.find({"assigned_to": current_user.id}, {"_id": 0}).to_list(1000)
    else:
        tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert datetime strings
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        elif 'created_at' not in task:
            task['created_at'] = datetime.now(timezone.utc)
        
        if isinstance(task.get('updated_at'), str):
            task['updated_at'] = datetime.fromisoformat(task['updated_at'])
        elif 'updated_at' not in task:
            task['updated_at'] = datetime.now(timezone.utc)
    
    return [TaskResponse(**task) for task in tasks]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get task by ID
    - Team members can only view their own tasks
    """
    db = get_database()
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check authorization for team members
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )
    
    # Convert datetime strings
    if isinstance(task.get('created_at'), str):
        task['created_at'] = datetime.fromisoformat(task['created_at'])
    elif 'created_at' not in task:
        task['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(task.get('updated_at'), str):
        task['updated_at'] = datetime.fromisoformat(task['updated_at'])
    elif 'updated_at' not in task:
        task['updated_at'] = datetime.now(timezone.utc)
    
    return TaskResponse(**task)

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update task
    - Team members can only update status of their own tasks
    - Admins and Managers can update all fields
    """
    db = get_database()
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Authorization checks
    if current_user.role == "team_member":
        if task["assigned_to"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )
        # Team members can only update status
        update_data = {"status": task_update.status} if task_update.status else {}
    else:
        # Admins and Managers can update all fields
        update_data = task_update.model_dump(exclude_unset=True)
        
        # If assigned_to is being updated, fetch new user details and log reassignment
        if "assigned_to" in update_data and update_data["assigned_to"] != task.get("assigned_to"):
            assigned_user = await db.users.find_one({"id": update_data["assigned_to"]}, {"_id": 0})
            if not assigned_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned user not found"
                )
            
            old_assignee = task.get("assigned_to_name", "Unassigned")
            new_assignee = assigned_user["full_name"]
            
            update_data["assigned_to_email"] = assigned_user["email"]
            update_data["assigned_to_name"] = new_assignee
            
            # Log task reassignment audit
            await log_audit(
                action_type="task_reassigned",
                user_id=current_user.id,
                user_name=current_user.full_name,
                user_email=current_user.email,
                task_id=task_id,
                metadata={
                    "task_title": task["title"],
                    "old_assignee": old_assignee,
                    "new_assignee": new_assignee,
                    "new_assignee_email": assigned_user["email"]
                }
            )
            
            # Create notification for new assignee
            await create_notification(
                user_id=update_data["assigned_to"],
                notification_type="task_assigned",
                message=f"Task '{task['title']}' has been reassigned to you by {current_user.full_name}",
                related_task_id=task_id
            )
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Validate status if provided
    if "status" in update_data:
        valid_statuses = ["todo", "in_progress", "completed", "cancelled"]
        if update_data["status"] not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Add completed_at timestamp when task is marked as completed
        if update_data["status"] == "completed" and task.get("status") != "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Create notification for status change
        if task.get("status") != update_data["status"]:
            # Notify assigned user if status changed by manager/admin
            if current_user.role != "team_member":
                await create_notification(
                    user_id=task["assigned_to"],
                    notification_type="status_changed",
                    message=f"Task '{task['title']}' status changed to: {update_data['status'].replace('_', ' ')}",
                    related_task_id=task_id
                )
            
            # Log status change audit
            await log_audit(
                action_type="status_changed",
                user_id=current_user.id,
                user_name=current_user.full_name,
                user_email=current_user.email,
                task_id=task_id,
                metadata={
                    "old_status": task.get("status"),
                    "new_status": update_data["status"],
                    "task_title": task["title"]
                }
            )
    
    # Update timestamp
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    
    # Fetch updated task
    updated_task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    # Convert datetime strings
    if isinstance(updated_task.get('created_at'), str):
        updated_task['created_at'] = datetime.fromisoformat(updated_task['created_at'])
    elif 'created_at' not in updated_task:
        updated_task['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(updated_task.get('updated_at'), str):
        updated_task['updated_at'] = datetime.fromisoformat(updated_task['updated_at'])
    elif 'updated_at' not in updated_task:
        updated_task['updated_at'] = datetime.now(timezone.utc)
    
    return TaskResponse(**updated_task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    DEPRECATED: Tasks should not be deleted
    Use PATCH to update status to 'cancelled' instead
    This endpoint is disabled for data integrity
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Task deletion is not allowed. Use status update to 'cancelled' instead."
    )

@router.patch("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Cancel a task (Admin and Manager only)
    - Sets status to 'cancelled'
    - Task remains in database but excluded from active workflows
    """
    db = get_database()
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    old_status = task.get("status")
    
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": "cancelled",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit
    await log_audit(
        action_type="task_cancelled",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=task_id,
        metadata={
            "task_title": task["title"],
            "old_status": old_status,
            "new_status": "cancelled"
        }
    )
    
    # Fetch updated task
    updated_task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    if isinstance(updated_task.get('created_at'), str):
        updated_task['created_at'] = datetime.fromisoformat(updated_task['created_at'])
    elif 'created_at' not in updated_task:
        updated_task['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(updated_task.get('updated_at'), str):
        updated_task['updated_at'] = datetime.fromisoformat(updated_task['updated_at'])
    elif 'updated_at' not in updated_task:
        updated_task['updated_at'] = datetime.now(timezone.utc)
    
    return TaskResponse(**updated_task)
