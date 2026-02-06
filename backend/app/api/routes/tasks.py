from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, BulkTaskUpdate, BulkTaskCancel, BulkTaskDelete, BulkOperationResponse
from app.models.task import TaskInDB
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user, require_role
from app.core.roles import NON_ADMIN_ROLES, MANAGER_ROLES
from app.services.notification_service import create_notification
from app.services.audit_service import log_audit
from app.services.email_service import send_task_assigned_email
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new task (All authenticated users)
    - Non-admin roles can assign to everyone except admins
    - Admins and Managers can assign to anyone
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
    
    # Non-admin roles cannot assign tasks to admins
    if current_user.role in NON_ADMIN_ROLES and assigned_user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign tasks to admins"
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
async def list_tasks(
    # Search parameters
    search: str = Query(None, description="Search in title and description"),
    # Filter parameters
    status: str = Query(None, description="Filter by status: todo, in_progress, completed, cancelled"),
    priority: str = Query(None, description="Filter by priority: low, medium, high"),
    assigned_to: str = Query(None, description="Filter by assigned user ID"),
    created_by: str = Query(None, description="Filter by creator user ID"),
    # Date filters
    due_date_from: str = Query(None, description="Due date from (YYYY-MM-DD)"),
    due_date_to: str = Query(None, description="Due date to (YYYY-MM-DD)"),
    created_from: str = Query(None, description="Created date from (YYYY-MM-DD)"),
    created_to: str = Query(None, description="Created date to (YYYY-MM-DD)"),
    # Overdue filter
    overdue: bool = Query(None, description="Filter overdue tasks only"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort by: created_at, due_date, priority, status, title"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    # Current user
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all tasks with search, filtering, sorting, and pagination.
    All authenticated users can see all tasks.
    
    Filters:
    - search: Search in title and description (case-insensitive)
    - status: todo, in_progress, completed, cancelled
    - priority: low, medium, high
    - assigned_to: User ID
    - created_by: User ID
    - due_date_from/to: Date range for due date
    - created_from/to: Date range for creation date
    - overdue: true to show only overdue tasks
    
    Sorting:
    - sort_by: created_at, due_date, priority, status, title
    - sort_order: asc, desc
    """
    db = get_database()
    
    # Build query
    query = {}
    
    # Text search (title and description)
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Status filter
    if status:
        valid_statuses = ["todo", "in_progress", "completed", "cancelled"]
        if status in valid_statuses:
            query["status"] = status
    
    # Priority filter
    if priority:
        valid_priorities = ["low", "medium", "high"]
        if priority in valid_priorities:
            query["priority"] = priority
    
    # Assigned to filter
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    # Created by filter
    if created_by:
        query["created_by"] = created_by
    
    # Due date range filter
    if due_date_from or due_date_to:
        query["due_date"] = {}
        if due_date_from:
            query["due_date"]["$gte"] = due_date_from
        if due_date_to:
            query["due_date"]["$lte"] = due_date_to
    
    # Created date range filter
    if created_from or created_to:
        created_filter = {}
        if created_from:
            created_filter["$gte"] = f"{created_from}T00:00:00"
        if created_to:
            created_filter["$lte"] = f"{created_to}T23:59:59"
        query["created_at"] = created_filter
    
    # Overdue filter
    if overdue:
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query["due_date"] = {"$lt": current_date}
        query["status"] = {"$nin": ["completed", "cancelled"]}
    
    # Sorting
    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by if sort_by in ["created_at", "due_date", "priority", "status", "title"] else "created_at"
    
    # Priority needs special handling for proper sorting
    if sort_field == "priority":
        # We'll sort in memory after fetching
        tasks = await db.tasks.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2), reverse=(sort_order == "desc"))
    elif sort_field == "title":
        # Title sorting needs case-insensitive collation
        tasks = await db.tasks.find(query, {"_id": 0}).sort(sort_field, sort_direction).collation({'locale': 'en', 'strength': 2}).skip(skip).limit(limit).to_list(limit)
    else:
        tasks = await db.tasks.find(query, {"_id": 0}).sort(sort_field, sort_direction).skip(skip).limit(limit).to_list(limit)
    
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

@router.get("/stats/summary")
async def get_task_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get task statistics summary for dashboard
    Returns counts by status, priority, and overdue tasks
    """
    db = get_database()
    
    # Get all tasks
    tasks = await db.tasks.find({}, {"_id": 0, "status": 1, "priority": 1, "due_date": 1, "assigned_to": 1}).to_list(10000)
    
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Calculate stats
    stats = {
        "total": len(tasks),
        "by_status": {
            "todo": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        },
        "by_priority": {
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "overdue": 0,
        "my_tasks": 0,
        "my_overdue": 0
    }
    
    for task in tasks:
        # By status
        status = task.get("status", "todo")
        if status in stats["by_status"]:
            stats["by_status"][status] += 1
        
        # By priority
        priority = task.get("priority", "medium")
        if priority in stats["by_priority"]:
            stats["by_priority"][priority] += 1
        
        # Overdue check
        due_date = task.get("due_date", "")
        is_overdue = due_date < current_date and status not in ["completed", "cancelled"]
        if is_overdue:
            stats["overdue"] += 1
        
        # My tasks
        if task.get("assigned_to") == current_user.id:
            stats["my_tasks"] += 1
            if is_overdue:
                stats["my_overdue"] += 1
    
    return stats
@router.post("/bulk/update", response_model=BulkOperationResponse)
async def bulk_update_tasks(
    bulk_data: BulkTaskUpdate,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Bulk update multiple tasks (Admin and Manager only)
    - Can update status, priority, or assigned_to
    - At least one update field must be provided
    """
    db = get_database()
    
    if not bulk_data.task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task IDs provided"
        )
    
    # Build update document
    update_fields = {}
    
    if bulk_data.status:
        valid_statuses = ["todo", "in_progress", "completed", "cancelled"]
        if bulk_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        update_fields["status"] = bulk_data.status
    
    if bulk_data.priority:
        valid_priorities = ["low", "medium", "high"]
        if bulk_data.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        update_fields["priority"] = bulk_data.priority
    
    if bulk_data.assigned_to:
        assigned_user = await db.users.find_one({"id": bulk_data.assigned_to}, {"_id": 0})
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found"
            )
        update_fields["assigned_to"] = bulk_data.assigned_to
        update_fields["assigned_to_email"] = assigned_user["email"]
        update_fields["assigned_to_name"] = assigned_user["full_name"]
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided"
        )
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Perform bulk update
    result = await db.tasks.update_many(
        {"id": {"$in": bulk_data.task_ids}},
        {"$set": update_fields}
    )
    
    # Log audit for bulk operation
    await log_audit(
        action_type="bulk_task_update",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=None,
        metadata={
            "task_count": result.modified_count,
            "task_ids": bulk_data.task_ids,
            "update_fields": list(update_fields.keys())
        }
    )
    
    return BulkOperationResponse(
        success=True,
        updated_count=result.modified_count,
        failed_count=len(bulk_data.task_ids) - result.modified_count,
        message=f"Successfully updated {result.modified_count} tasks"
    )


@router.post("/bulk/cancel", response_model=BulkOperationResponse)
async def bulk_cancel_tasks(
    bulk_data: BulkTaskCancel,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Bulk cancel multiple tasks (Admin and Manager only)
    - Sets status to 'cancelled' for all specified tasks
    - Tasks remain in database for audit trail
    """
    db = get_database()
    
    if not bulk_data.task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task IDs provided"
        )
    
    # Get task titles for audit log
    tasks = await db.tasks.find(
        {"id": {"$in": bulk_data.task_ids}},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(len(bulk_data.task_ids))
    
    # Perform bulk cancel
    result = await db.tasks.update_many(
        {"id": {"$in": bulk_data.task_ids}},
        {"$set": {
            "status": "cancelled",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit for bulk cancel
    await log_audit(
        action_type="bulk_task_cancel",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=None,
        metadata={
            "task_count": result.modified_count,
            "task_ids": bulk_data.task_ids,
            "task_titles": [t["title"] for t in tasks]
        }
    )
    
    return BulkOperationResponse(
        success=True,
        updated_count=result.modified_count,
        failed_count=len(bulk_data.task_ids) - result.modified_count,
        message=f"Successfully cancelled {result.modified_count} tasks"
    )


@router.delete("/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete_tasks(
    bulk_data: BulkTaskDelete,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Bulk delete multiple tasks permanently (Admin and Manager only)
    - WARNING: This permanently removes tasks from the database
    - Also deletes associated comments and attachments
    """
    db = get_database()
    
    if not bulk_data.task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No task IDs provided"
        )
    
    # Get task titles for audit log before deletion
    tasks = await db.tasks.find(
        {"id": {"$in": bulk_data.task_ids}},
        {"_id": 0, "id": 1, "title": 1}
    ).to_list(len(bulk_data.task_ids))
    
    # Delete associated comments
    await db.comments.delete_many({"task_id": {"$in": bulk_data.task_ids}})
    
    # Delete associated attachments (and their files)
    attachments = await db.attachments.find(
        {"task_id": {"$in": bulk_data.task_ids}},
        {"_id": 0, "file_path": 1}
    ).to_list(1000)
    
    import os
    for attachment in attachments:
        if os.path.exists(attachment.get("file_path", "")):
            try:
                os.remove(attachment["file_path"])
            except:
                pass
    
    await db.attachments.delete_many({"task_id": {"$in": bulk_data.task_ids}})
    
    # Delete tasks
    result = await db.tasks.delete_many({"id": {"$in": bulk_data.task_ids}})
    
    # Log audit for bulk delete
    await log_audit(
        action_type="bulk_task_delete",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        task_id=None,
        metadata={
            "task_count": result.deleted_count,
            "task_ids": bulk_data.task_ids,
            "task_titles": [t["title"] for t in tasks]
        }
    )
    
    return BulkOperationResponse(
        success=True,   
        updated_count=result.deleted_count,
        failed_count=len(bulk_data.task_ids) - result.deleted_count,
        message=f"Successfully deleted {result.deleted_count} tasks permanently"
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get task by ID - All users can view any task
    """
    db = get_database()
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
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



# ==================== BULK OPERATIONS (Admin/Manager Only) ====================

