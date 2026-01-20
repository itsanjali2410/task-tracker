from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from app.schemas.attachment import UserProductivity, TeamOverview
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/reports", tags=["Reports"])

def calculate_productivity_score(
    total_tasks: int,
    completed: int,
    completed_on_time: int,
    overdue: int
) -> float:
    """
    Calculate productivity score (0-100)
    - 40% weight: completion rate
    - 30% weight: on-time completion rate
    - 30% weight: inverse overdue rate
    """
    if total_tasks == 0:
        return 0.0
    
    completion_rate = (completed / total_tasks) * 100
    on_time_rate = (completed_on_time / total_tasks) * 100 if total_tasks > 0 else 0
    overdue_penalty = (overdue / total_tasks) * 100 if total_tasks > 0 else 0
    
    score = (
        (completion_rate * 0.4) +
        (on_time_rate * 0.3) +
        ((100 - overdue_penalty) * 0.3)
    )
    
    return round(min(max(score, 0), 100), 2)

@router.get("/user-productivity", response_model=List[UserProductivity])
async def get_user_productivity(
    user_id: Optional[str] = Query(None, description="Filter by specific user (optional)"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get productivity metrics for users
    - Managers/Admins can view all users or specific user
    - Team members can only view their own stats
    """
    db = get_database()
    
    # Authorization check
    if current_user.role == "team_member":
        # Team members can only view their own stats
        target_user_id = current_user.id
    else:
        # Managers/Admins can view all or specific user
        target_user_id = user_id if user_id else None
    
    # Build query
    if target_user_id:
        users = await db.users.find({"id": target_user_id}, {"_id": 0}).to_list(1)
    else:
        users = await db.users.find({}, {"_id": 0}).to_list(1000)
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    productivity_stats = []
    
    for user in users:
        user_id = user["id"]
        
        # Get all tasks assigned to this user
        tasks = await db.tasks.find({"assigned_to": user_id}, {"_id": 0}).to_list(1000)
        
        total_tasks = len(tasks)
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        tasks_completed = len(completed_tasks)
        
        # Calculate on-time completion
        tasks_completed_on_time = 0
        total_completion_time = 0
        
        for task in completed_tasks:
            # Check if task has completed_at field
            completed_at = task.get("completed_at")
            if completed_at:
                if isinstance(completed_at, str):
                    completed_at = datetime.fromisoformat(completed_at)
                
                # Parse due_date
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                except:
                    # If due_date is just a date string, convert to datetime
                    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                # Check if completed on time
                if completed_at <= due_date:
                    tasks_completed_on_time += 1
                
                # Calculate completion time
                created_at = task.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    completion_time = (completed_at - created_at).total_seconds() / 3600  # hours
                    total_completion_time += completion_time
        
        # Calculate average completion time
        average_completion_time = (
            total_completion_time / tasks_completed if tasks_completed > 0 else 0
        )
        
        # Calculate overdue tasks (not completed and past due date)
        overdue_tasks = 0
        current_time = datetime.now(timezone.utc)
        
        for task in tasks:
            if task["status"] != "completed":
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                except:
                    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                if current_time > due_date:
                    overdue_tasks += 1
        
        # Calculate productivity score
        productivity_score = calculate_productivity_score(
            total_tasks,
            tasks_completed,
            tasks_completed_on_time,
            overdue_tasks
        )
        
        productivity_stats.append(UserProductivity(
            user_id=user["id"],
            user_name=user["full_name"],
            user_email=user["email"],
            total_tasks_assigned=total_tasks,
            tasks_completed=tasks_completed,
            tasks_completed_on_time=tasks_completed_on_time,
            overdue_tasks=overdue_tasks,
            average_completion_time_hours=round(average_completion_time, 2),
            productivity_score=productivity_score
        ))
    
    return productivity_stats

@router.get("/team-overview", response_model=TeamOverview)
async def get_team_overview(
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Get team-wide productivity overview
    - Only Managers and Admins can access
    """
    db = get_database()
    
    # Get all users
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    total_users = len(users)
    
    # Get all tasks
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(10000)
    total_tasks = len(tasks)
    
    # Calculate overall stats
    completed_tasks = [t for t in tasks if t["status"] == "completed"]
    total_completed = len(completed_tasks)
    
    # Calculate overdue tasks
    overdue_tasks = 0
    current_time = datetime.now(timezone.utc)
    
    for task in tasks:
        if task["status"] != "completed":
            try:
                due_date = datetime.fromisoformat(task["due_date"])
            except:
                due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            if current_time > due_date:
                overdue_tasks += 1
    
    # Get user productivity stats
    user_stats_response = await get_user_productivity(None, current_user)
    
    # Calculate average productivity score
    if user_stats_response:
        avg_score = sum(u.productivity_score for u in user_stats_response) / len(user_stats_response)
    else:
        avg_score = 0.0
    
    return TeamOverview(
        total_users=total_users,
        total_tasks=total_tasks,
        total_completed=total_completed,
        total_overdue=overdue_tasks,
        average_productivity_score=round(avg_score, 2),
        user_stats=user_stats_response
    )
