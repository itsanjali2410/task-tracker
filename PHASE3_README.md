# TripStars Task Management System - PHASE 3 Features

## Overview

Phase 3 extends the TripStars system with file attachments, productivity tracking, and enhanced reporting capabilities.

## New Features

### 1. File Attachments

**Backend API Endpoints:**
- `POST /api/attachments?task_id={task_id}` - Upload file to task
- `GET /api/attachments/task/{task_id}` - List task attachments
- `GET /api/attachments/{attachment_id}/download` - Download file
- `DELETE /api/attachments/{attachment_id}` - Delete attachment

**File Specifications:**
- Allowed types: PDF, JPG, JPEG, PNG, DOC, DOCX
- Maximum size: 10MB per file
- Storage: `/app/uploads/` directory
- Cloud-ready structure

**Security:**
- Only authenticated users can upload
- Team members can only upload to their assigned tasks
- Only uploader or admin can delete attachments
- Download requires task access permission

**Frontend:**
- Attachments tab in Task Detail page
- Drag-and-drop file upload interface
- File list with size, uploader, and date
- Download and delete actions
- Visual feedback for upload progress

### 2. Productivity Tracking & Reports

**Backend Calculations:**

Productivity Score (0-100) based on:
- 40% - Task completion rate
- 30% - On-time completion rate
- 30% - Inverse overdue rate

**Metrics per User:**
- `total_tasks_assigned` - All tasks assigned to user
- `tasks_completed` - Successfully completed tasks
- `tasks_completed_on_time` - Completed before/on due date
- `overdue_tasks` - Incomplete tasks past due date
- `average_completion_time_hours` - Average time to complete
- `productivity_score` - Overall performance score (0-100)

**API Endpoints:**
- `GET /api/reports/user-productivity?user_id={id}` - Individual stats
- `GET /api/reports/team-overview` - Team-wide analytics

**Authorization:**
- Managers/Admins: View all users and team overview
- Team Members: View only their own stats

### 3. Enhanced Dashboards

**For All Users:**
- Task statistics (Total, To Do, In Progress, Completed)
- Recent tasks list
- Personal productivity score card (if tasks assigned)

**For Managers/Admins:**
- New "Reports" page with team productivity overview
- Individual user performance table
- Sortable metrics columns
- Team-wide statistics

**Team Member Dashboard:**
- Productivity score with detailed metrics
- Completion rates and on-time performance
- Overdue task alerts
- Average completion time

## Database Schema Updates

### New Collection: attachments

```javascript
{
  id: String,
  task_id: String,
  uploaded_by: String,
  uploaded_by_name: String,
  uploaded_by_email: String,
  file_name: String,
  file_type: String, // pdf, jpg, png, doc, docx
  file_size: Number, // bytes
  file_path: String,
  uploaded_at: DateTime
}
```

### Tasks Collection Updates

Added field:
```javascript
{
  ...existing fields,
  completed_at: DateTime // Timestamp when task status changed to completed
}
```

## Usage Examples

### Upload File to Task

```bash
curl -X POST "https://api.tripstars.com/api/attachments?task_id=task-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### Get User Productivity

```bash
curl -X GET "https://api.tripstars.com/api/reports/user-productivity?user_id=user-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
[
  {
    "user_id": "uuid",
    "user_name": "John Doe",
    "user_email": "john@tripstars.com",
    "total_tasks_assigned": 10,
    "tasks_completed": 8,
    "tasks_completed_on_time": 6,
    "overdue_tasks": 1,
    "average_completion_time_hours": 24.5,
    "productivity_score": 75.6
  }
]
```

### Get Team Overview

```bash
curl -X GET "https://api.tripstars.com/api/reports/team-overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "total_users": 15,
  "total_tasks": 150,
  "total_completed": 120,
  "total_overdue": 10,
  "average_productivity_score": 78.4,
  "user_stats": [...]
}
```

## Frontend Navigation

### Updated Routes

- `/dashboard` - Enhanced with productivity scores (All roles)
- `/tasks/:taskId` - Task detail with Attachments tab (All roles)
- `/reports` - Team productivity reports (Manager/Admin only)

### New Components

1. **TaskDetail.js** (Updated)
   - Tabs: Comments / Attachments
   - File upload interface
   - Attachment list with actions

2. **Reports.js** (New)
   - Team overview statistics
   - User performance table
   - Productivity score visualization

3. **Dashboard.js** (Updated)
   - Personal productivity score card
   - Detailed metrics breakdown

## Security Considerations

### File Upload Security

- File type validation (whitelist approach)
- File size limits enforced
- Unique file naming (UUID-based)
- Authorization checks before upload/download
- Files stored outside web root

### API Security

- All endpoints require JWT authentication
- Role-based access control enforced
- Team members can only access their own data
- Managers/Admins have full team visibility

### Data Privacy

- User productivity metrics only visible to:
  - The user themselves
  - Managers and Admins
- Team members cannot view other users' stats

## Performance Considerations

### Productivity Calculations

- Calculations performed on-demand
- Results not cached (always current)
- Optimized MongoDB queries
- Suitable for teams up to 1000 users

### File Storage

- Local storage for development
- Cloud-ready structure for production
- Recommended: AWS S3, Google Cloud Storage, or Azure Blob
- Consider CDN for large files

## Migration Guide

### From Phase 2 to Phase 3

No breaking changes. Phase 3 is additive only.

**Optional: Add completed_at to existing tasks**

```javascript
// MongoDB command to set completed_at for already completed tasks
db.tasks.updateMany(
  { status: "completed", completed_at: { $exists: false } },
  { $set: { completed_at: new Date() } }
);
```

## Production Deployment

### Environment Setup

1. Create uploads directory:
```bash
mkdir -p /app/uploads
chmod 755 /app/uploads
```

2. Update production config for cloud storage (optional):
```python
# app/core/config.py
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
CLOUD_STORAGE_ENABLED = os.getenv("CLOUD_STORAGE_ENABLED", "false")
CLOUD_STORAGE_BUCKET = os.getenv("CLOUD_STORAGE_BUCKET", "")
```

3. Restart services:
```bash
sudo supervisorctl restart backend frontend
```

## Testing

### Test File Upload

```python
# Test file upload
import requests

token = "YOUR_JWT_TOKEN"
task_id = "TASK_UUID"

with open("test.pdf", "rb") as f:
    response = requests.post(
        f"http://localhost:8001/api/attachments?task_id={task_id}",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f}
    )

print(response.json())
```

### Test Productivity API

```python
# Get user productivity
response = requests.get(
    "http://localhost:8001/api/reports/user-productivity",
    headers={"Authorization": f"Bearer {token}"}
)

print(response.json())
```

## Known Limitations

1. **File Storage**: Currently local filesystem. Recommended to migrate to cloud storage for production.

2. **Productivity Calculations**: Real-time calculations may be slow for very large datasets (>10,000 tasks).

3. **File Preview**: No in-browser preview. Files must be downloaded.

## Future Enhancements

- [ ] Cloud storage integration (S3, GCS, Azure)
- [ ] File preview for PDFs and images
- [ ] Batch file upload
- [ ] File versioning
- [ ] Advanced reporting with date range filters
- [ ] Export reports to CSV/PDF
- [ ] Real-time productivity dashboard
- [ ] Email notifications for productivity milestones

## Support

For issues related to Phase 3 features:
- File upload errors: Check file size and type
- Productivity calculation questions: Review metrics calculation formula
- Permission errors: Verify user role and task ownership

## API Documentation

Full interactive API documentation available at:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc
