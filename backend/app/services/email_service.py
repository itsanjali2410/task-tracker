import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not EMAIL_ENABLED:
        logger.info(f"Email sending disabled. Would send to {to_email}: {subject}")
        return True
    
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        logger.warning("Email configuration incomplete. Skipping email send.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_task_assigned_email(to_email: str, to_name: str, task_title: str, task_due_date: str, assigned_by: str):
    """
    Send task assignment notification email
    """
    subject = f"New Task Assigned: {task_title}"
    body = f"""Hello {to_name},

You have been assigned a new task in TripStars Task Management System.

Task: {task_title}
Due Date: {task_due_date}
Assigned By: {assigned_by}

Please log in to view the task details and start working on it.

Best regards,
TripStars Task Management System
"""
    return send_email(to_email, subject, body)

def send_task_overdue_email(to_email: str, to_name: str, task_title: str, task_due_date: str):
    """
    Send overdue task reminder email
    """
    subject = f"Task Overdue: {task_title}"
    body = f"""Hello {to_name},

This is a reminder that the following task is now overdue:

Task: {task_title}
Due Date: {task_due_date}
Status: OVERDUE

Please complete this task as soon as possible or update its status.

Best regards,
TripStars Task Management System
"""
    return send_email(to_email, subject, body)

def send_comment_notification_email(to_email: str, to_name: str, task_title: str, commenter_name: str, comment_preview: str):
    """
    Send comment notification email
    """
    subject = f"New Comment on Task: {task_title}"
    body = f"""Hello {to_name},

{commenter_name} has added a comment to a task you're involved with:

Task: {task_title}
Comment: {comment_preview[:100]}{'...' if len(comment_preview) > 100 else ''}

Please log in to view the full comment and respond if needed.

Best regards,
TripStars Task Management System
"""
    return send_email(to_email, subject, body)
