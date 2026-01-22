# TripStars Task Management System - PHASE 4 Features

## Overview

Phase 4 adds real-time notifications, email alerts, background automation, and comprehensive audit logging to the TripStars system.

## New Features

### 1. In-App Notifications

**MongoDB Collection: notifications**
```javascript
{
  id: String,
  user_id: String,
  type: String, // task_assigned, task_overdue, comment_added, file_uploaded, status_changed
  related_task_id: String (optional),
  message: String,
  is_read: Boolean,
  created_at: DateTime
}
```

**API Endpoints:**
- `GET /api/notifications` - List current user's notifications
- `GET /api/notifications/unread-count` - Get unread count
- `POST /api/notifications/mark-read/{id}` - Mark single notification as read
- `POST /api/notifications/mark-all-read` - Mark all notifications as read

**Notification Triggers:**
- Task assigned → Notify assigned user
- Task overdue → Notify assigned user (via background job)
- Comment added → Notify task participants (assigned user + creator)
- File uploaded → Notify task participants
- Status changed → Notify assigned user (when changed by manager/admin)

**Frontend UI:**
- Notification bell icon in header
- Unread count badge
- Dropdown with notification list
- Mark as read functionality
- Click to navigate to related task

### 2. Email Notifications

**SMTP Configuration:**
Email sending via SMTP with environment variables:
- `EMAIL_ENABLED` - Enable/disable email sending (true/false)
- `SMTP_HOST` - SMTP server host (e.g., smtp.gmail.com)
- `SMTP_PORT` - SMTP port (e.g., 587 for TLS)
- `SMTP_USER` - SMTP username/email
- `SMTP_PASSWORD` - SMTP password/app password
- `SMTP_FROM_EMAIL` - From email address (optional, defaults to SMTP_USER)

**Email Templates:**
1. **Task Assignment**
   - Subject: "New Task Assigned: {task_title}"
   - Includes: task title, due date, assigned by

2. **Task Overdue**
   - Subject: "Task Overdue: {task_title}"
   - Includes: task title, due date, status

3. **Comment Notification**
   - Subject: "New Comment on Task: {task_title}"
   - Includes: commenter name, comment preview

**Email Triggers:**
- Task assigned → Immediate email to assigned user
- Task overdue → Daily reminder email (via background job)
- Comment added → Email to task participants

### 3. Background Jobs / Automation

**Scheduler: APScheduler**
- Async background job scheduler
- Runs periodic tasks without blocking main application

**Overdue Task Checker:**
- **Frequency:** Every 1 hour
- **Function:** `check_overdue_tasks()`
- **Actions:**
  1. Find tasks with status != "completed" and due_date < current_time
  2. Check if overdue notification sent within last 24 hours
  3. Create in-app notification
  4. Send email reminder
  5. Prevent duplicate notifications

**Features:**
- Automatic startup with application
- Graceful shutdown on application stop
- Error handling and logging
- Idempotent (safe to run multiple times)

### 4. Audit Logs

**MongoDB Collection: audit_logs**
```javascript
{
  id: String,
  action_type: String, // task_created, task_updated, status_changed, file_uploaded, comment_added, user_created
  user_id: String,
  user_name: String,
  user_email: String,
  task_id: String (optional),
  metadata: Object, // old_value, new_value, etc.
  timestamp: DateTime
}
```

**API Endpoints:**
- `GET /api/audit-logs` - List audit logs (Admin/Manager only)
  - Query params: `limit`, `action_type`, `user_id`, `task_id`

**Automatic Logging For:**
- Task creation (task_created)
- Task updates (task_updated)
- Status changes (status_changed)
- File uploads (file_uploaded)
- Comment additions (comment_added)
- User creation (user_created)

**Frontend UI:**
- Audit Logs page (Admin/Manager only)
- Filter by action type
- Adjustable result limit (50-500)
- Detailed table view with user, action, timestamp
- Metadata display

### 5. Security & Access Control

**Notifications:**
- Users can only view their own notifications
- JWT authentication required
- Notification IDs validated against user_id

**Audit Logs:**
- Only Admin and Manager roles can access
- Read-only access (no delete/modify)
- JWT authentication required

**Background Jobs:**
- Run with system privileges
- No user authentication required
- Error logging for monitoring

## Setup & Configuration

### 1. Environment Variables

Add to `/app/backend/.env`:
```bash
# Email Configuration (Phase 4)
EMAIL_ENABLED=false  # Set to true to enable email sending
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@tripstars.com
```

**For Gmail:**
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in SMTP_PASSWORD

**For Other Providers:**
- SendGrid: smtp.sendgrid.net, port 587
- Mailgun: smtp.mailgun.org, port 587
- AWS SES: email-smtp.{region}.amazonaws.com, port 587

### 2. Database Setup

No migration required. Collections are created automatically on first insert.

**Manual Index Creation (Optional for performance):**
```javascript
// MongoDB commands
db.notifications.createIndex({ "user_id": 1, "created_at": -1 });
db.notifications.createIndex({ "user_id": 1, "is_read": 1 });
db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "action_type": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 });
```

### 3. Testing Email Configuration

Test email sending:
```python
# Python test script
from app.services.email_service import send_email

result = send_email(
    to_email="test@example.com",
    subject="Test Email",
    body="This is a test email from TripStars"
)

print(f"Email sent: {result}")
```

## Usage Examples

### Get Notifications

```bash
curl -X GET "https://api.tripstars.com/api/notifications?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
[
  {
    "id": "uuid",
    "user_id": "user-uuid",
    "type": "task_assigned",
    "related_task_id": "task-uuid",
    "message": "You have been assigned a new task: 'Prepare travel itinerary'",
    "is_read": false,
    "created_at": "2024-01-20T10:00:00Z"
  }
]
```

### Get Unread Count

```bash
curl -X GET "https://api.tripstars.com/api/notifications/unread-count" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "unread_count": 5
}
```

### Mark as Read

```bash
curl -X POST "https://api.tripstars.com/api/notifications/mark-read/{notification_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Audit Logs

```bash
curl -X GET "https://api.tripstars.com/api/audit-logs?limit=100&action_type=task_created" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
[
  {
    "id": "uuid",
    "action_type": "task_created",
    "user_id": "user-uuid",
    "user_name": "John Doe",
    "user_email": "john@tripstars.com",
    "task_id": "task-uuid",
    "metadata": {
      "task_title": "Prepare travel itinerary",
      "assigned_to": "Jane Smith",
      "priority": "high"
    },
    "timestamp": "2024-01-20T10:00:00Z"
  }
]
```

## Technical Details

### Background Scheduler

**Implementation:** APScheduler with AsyncIOScheduler
- Runs in same process as FastAPI application
- Uses asyncio for non-blocking operations
- Automatically started on application startup
- Gracefully shut down on application stop

**Job Configuration:**
```python
scheduler.add_job(
    check_overdue_tasks,
    'interval',
    hours=1,  # Run every hour
    id='check_overdue_tasks',
    replace_existing=True
)
```

**Preventing Duplicate Notifications:**
- Check existing notifications for same task + user + type
- Only send if no notification in last 24 hours
- Ensures users don't get spammed with reminders

### Email Service

**Architecture:**
- Service layer pattern (app/services/email_service.py)
- Separate functions for each email type
- Graceful degradation (continues if email fails)
- Logging for debugging

**Error Handling:**
- Catches SMTP exceptions
- Logs errors without breaking application flow
- Returns boolean success status
- Silent failure if EMAIL_ENABLED=false

### Notification Service

**Architecture:**
- Service layer pattern (app/services/notification_service.py)
- Async operations for MongoDB
- Reusable functions for creating/reading notifications
- Error logging

**Integration Points:**
- Called from task routes
- Called from comment routes
- Called from attachment routes
- Called from background jobs

### Audit Service

**Architecture:**
- Service layer pattern (app/services/audit_service.py)
- Async MongoDB operations
- Immutable logs (no update/delete)
- Flexible metadata storage

**Best Practices:**
- Log all significant actions
- Include enough context for debugging
- Store user information (name, email)
- Include old/new values for changes

## Frontend Implementation

### NotificationBell Component

**Features:**
- Real-time unread count
- Polling every 30 seconds
- Dropdown with notification list
- Click-to-navigate to related task
- Mark individual or all as read
- Visual distinction for unread items

**Styling:**
- Red badge for unread count
- Blue highlight for unread notifications
- Icon representation by notification type
- Responsive dropdown

### AuditLogs Page

**Features:**
- Filterable by action type
- Adjustable result limit
- Tabular display
- Color-coded action types
- Metadata display
- Timestamps

**Access Control:**
- Only visible to Admin and Manager
- Protected route in App.js
- Navigation item only shown to authorized roles

## Performance Considerations

### Notifications

**Polling vs WebSocket:**
- Current: HTTP polling every 30 seconds
- Trade-off: Simpler implementation, good enough for most use cases
- Future: WebSocket for real-time push

**Database Queries:**
- Index on user_id + created_at for fast retrieval
- Limit result sets (default 50, max 100)
- Pagination can be added if needed

### Background Jobs

**Resource Usage:**
- Minimal CPU usage (runs once per hour)
- Async operations don't block main thread
- Suitable for small to medium deployments

**Scaling:**
- For larger deployments, use external scheduler (Celery, AWS Lambda)
- Current implementation works for <1000 users

### Email Sending

**Synchronous:**
- Email sending is synchronous (blocks briefly)
- Acceptable for low volume
- For high volume, use async email service (SendGrid API, AWS SES)

## Monitoring & Debugging

### Logs

**Application Logs:**
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Look for:
# - "Notification created for user..."
# - "Email sent successfully to..."
# - "Overdue task check complete..."
# - "Audit log created..."
```

**Scheduler Logs:**
```bash
# Scheduler startup
INFO:apscheduler.scheduler:Scheduler started
INFO:app.services.scheduler:Background scheduler started

# Job execution
INFO:app.services.scheduler:Running overdue task check...
INFO:app.services.scheduler:Overdue task check complete. Sent X notifications.
```

### Common Issues

**Email Not Sending:**
1. Check EMAIL_ENABLED=true
2. Verify SMTP credentials
3. Check SMTP_HOST and SMTP_PORT
4. Review email service logs
5. Test with Gmail app password

**Notifications Not Appearing:**
1. Check MongoDB connection
2. Verify notification creation in logs
3. Check frontend API calls
4. Verify JWT token is valid

**Background Job Not Running:**
1. Check scheduler startup logs
2. Verify APScheduler installed
3. Check for Python errors in logs
4. Ensure application started properly

## Security Best Practices

**Email Credentials:**
- Never commit SMTP_PASSWORD to git
- Use environment variables
- Use app passwords (not main password)
- Rotate credentials regularly

**Notifications:**
- Always validate user_id matches authenticated user
- Never expose other users' notifications
- Sanitize notification messages

**Audit Logs:**
- Immutable (no delete/edit)
- Secure admin/manager access only
- Include enough context for forensics
- Regular backups recommended

## Future Enhancements

- [ ] WebSocket for real-time notifications
- [ ] Email templates with HTML formatting
- [ ] Notification preferences (per-user settings)
- [ ] Push notifications (mobile/web)
- [ ] Advanced audit log filters (date range, search)
- [ ] Audit log export (CSV/JSON)
- [ ] Notification grouping/threading
- [ ] Email digest (daily/weekly summaries)
- [ ] Custom notification rules
- [ ] Slack/Teams integration

## Troubleshooting

### Scheduler Not Starting

```bash
# Check if APScheduler is installed
pip list | grep -i apscheduler

# Install if missing
pip install apscheduler==3.10.4

# Restart backend
sudo supervisorctl restart backend
```

### Duplicate Notifications

The system prevents duplicates by:
1. Checking existing notifications
2. Only creating if none sent in last 24 hours
3. Using unique combination: user_id + task_id + type

If duplicates still occur:
- Check system time is correct
- Review notification creation logic
- Check for multiple running instances

### Email Bouncing

Common causes:
- Invalid recipient email
- SMTP server blocking
- Daily sending limits exceeded
- Email marked as spam

Solutions:
- Verify email addresses
- Use reputable SMTP provider
- Implement email verification
- Add SPF/DKIM records

## API Documentation

Full interactive API documentation available at:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

## Support

For Phase 4 specific issues:
- Notification problems: Check MongoDB and notification service logs
- Email issues: Verify SMTP configuration and credentials
- Background job issues: Check scheduler logs and APScheduler installation
- Audit log questions: Review audit service implementation

---

**Phase 4 Summary:**
- ✅ In-app notifications with bell icon
- ✅ Email notifications via SMTP
- ✅ Background job scheduler for overdue tasks
- ✅ Comprehensive audit logging
- ✅ Frontend UI for all features
- ✅ No breaking changes to previous phases
