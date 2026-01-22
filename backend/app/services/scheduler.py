from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from app.db.mongodb import get_database
from app.services.notification_service import create_notification
from app.services.email_service import send_task_overdue_email
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def check_overdue_tasks():
    """
    Background job to check for overdue tasks and send notifications
    Runs periodically to find tasks that are overdue and not yet notified
    """
    try:
        logger.info("Running overdue task check...")
        db = get_database()
        
        current_time = datetime.now(timezone.utc)
        
        # Find tasks that are overdue and not completed
        tasks = await db.tasks.find({
            "status": {"$ne": "completed"}
        }, {"_id": 0}).to_list(1000)
        
        notified_count = 0
        
        for task in tasks:
            try:
                # Parse due date
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    if due_date.tzinfo is None:
                        due_date = due_date.replace(tzinfo=timezone.utc)
                except:
                    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                # Check if task is overdue
                if current_time > due_date:
                    # Check if we already sent an overdue notification recently (within 24 hours)
                    existing_notification = await db.notifications.find_one({
                        "related_task_id": task["id"],
                        "type": "task_overdue",
                        "user_id": task["assigned_to"]
                    })
                    
                    # If no notification exists or it's been more than 24 hours, send new one
                    should_notify = True
                    if existing_notification:
                        notif_created = existing_notification.get("created_at")
                        if isinstance(notif_created, str):
                            notif_created = datetime.fromisoformat(notif_created)
                        
                        # Check if notification was created within last 24 hours
                        if (current_time - notif_created).total_seconds() < 86400:
                            should_notify = False
                    
                    if should_notify:
                        # Create notification
                        await create_notification(
                            user_id=task["assigned_to"],
                            notification_type="task_overdue",
                            message=f"Task '{task['title']}' is overdue (due: {task['due_date']})",
                            related_task_id=task["id"]
                        )
                        
                        # Send email (if configured)
                        user = await db.users.find_one({"id": task["assigned_to"]}, {"_id": 0})
                        if user:
                            send_task_overdue_email(
                                to_email=user["email"],
                                to_name=user["full_name"],
                                task_title=task["title"],
                                task_due_date=task["due_date"]
                            )
                        
                        notified_count += 1
                        logger.info(f"Overdue notification sent for task: {task['title']}")
            
            except Exception as e:
                logger.error(f"Error processing task {task.get('id')}: {str(e)}")
                continue
        
        logger.info(f"Overdue task check complete. Sent {notified_count} notifications.")
    
    except Exception as e:
        logger.error(f"Error in overdue task check: {str(e)}")

def start_scheduler():
    """Start the background scheduler"""
    # Check for overdue tasks every hour
    scheduler.add_job(
        check_overdue_tasks,
        'interval',
        hours=1,
        id='check_overdue_tasks',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started")

def shutdown_scheduler():
    """Shutdown the background scheduler"""
    scheduler.shutdown()
    logger.info("Background scheduler stopped")
