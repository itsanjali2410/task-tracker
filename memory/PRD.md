# TripStars Task Management System - Product Requirements Document

## Overview
TripStars is an internal Task Management System for a travel company, built to manage tasks, assignments, reporting, collaboration, and real-time communication across teams.

**Tech Stack**: FastAPI (Python) + React + MongoDB (Atlas compatible) + WebSocket

---

## User Personas & Roles

### Admin
- Full system access
- User management (CRUD for all roles)
- View all reports and audit logs
- Cannot deactivate own account

### Manager  
- View all tasks and reports
- Cannot manage users
- Can cancel tasks

### Sales / Operations / Marketing / Accounts / Team Member
- **See ALL tasks** across the organization
- Create tasks and assign to other staff (not admins)
- Add comments and attachments to tasks
- Participate in one-to-one and group chats
- Receive notifications
- Cannot manage users, reports, or audit logs

---

## Core Features

### Phase 1-6: Foundation through Chat (COMPLETE)
- User authentication with JWT + Refresh tokens
- Role-based access control
- Task CRUD with comments and attachments
- Productivity reports and dashboards
- Notifications (in-app + email + WebSocket)
- Background scheduler
- Audit logging
- User Management CRUD frontend
- Real-time Chat (DM + Groups)

### Phase 7: Extended Roles & Chat Enhancements (COMPLETE)
- New Roles: Sales, Operations, Marketing, Accounts
- Chat: Pin conversations and messages
- Chat: Search messages

### Phase 8: All Users See All Tasks + Search/Filter (COMPLETE - Jan 23, 2026)
- **All Users See All Tasks**
  - Removed role-based task visibility restrictions
  - All authenticated users can view all tasks across the organization
  
- **Task Search**
  - Search by title (case-insensitive)
  - Search by description (case-insensitive)
  - Debounced search input in frontend
  
- **Task Filters**
  - Filter by status: todo, in_progress, completed, cancelled
  - Filter by priority: low, medium, high
  - Filter by assigned user
  - Filter by due date range (from/to)
  - Filter overdue tasks only
  
- **Task Sorting**
  - Sort by: created_at, due_date, priority, status, title
  - Sort order: ascending or descending
  
- **Pagination**
  - Skip and limit parameters
  - Up to 500 records per request
  
- **Task Stats Dashboard**
  - Total tasks count
  - Count by status (todo, in_progress, completed, cancelled)
  - Count by priority (high, medium, low)
  - Overdue tasks count
  - My tasks count

---

## API Endpoints

### Tasks (Updated)
| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/tasks` | GET | All Staff | List all tasks with search/filter/sort |
| `/api/tasks/stats/summary` | GET | All Staff | Get task statistics |
| `/api/tasks` | POST | All Staff | Create task |
| `/api/tasks/{id}` | GET | All Staff | Get task details |
| `/api/tasks/{id}` | PATCH | All Staff | Update task |
| `/api/tasks/{id}/cancel` | PATCH | All Staff | Cancel task |

### Task Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title and description |
| `status` | string | Filter: todo, in_progress, completed, cancelled |
| `priority` | string | Filter: low, medium, high |
| `assigned_to` | string | Filter by user ID |
| `due_date_from` | string | Filter: YYYY-MM-DD |
| `due_date_to` | string | Filter: YYYY-MM-DD |
| `overdue` | boolean | Show only overdue tasks |
| `sort_by` | string | Sort: created_at, due_date, priority, status, title |
| `sort_order` | string | Sort order: asc, desc |
| `skip` | integer | Pagination offset |
| `limit` | integer | Max records (1-500) |

---

## Valid Roles

```python
VALID_ROLES = [
    "admin",
    "manager", 
    "team_member",  # Legacy
    "sales",
    "operations",
    "marketing",
    "accounts"
]
```

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tripstars.com | Admin@123 |
| Manager | manager@tripstars.com | Manager@123 |
| Team Member | member@tripstars.com | Member@123 |
| Sales | sales@tripstars.com | Sales@123 |

---

## Deployment

See **DEPLOYMENT_GUIDE.md** for:
- MongoDB Atlas setup
- PM2 + Nginx configuration
- SSL certificate setup
- Environment variables reference

---

## Testing Status

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 1-5 | 23 | ✅ |
| Phase 6 | 27 | ✅ |
| Phase 7 | 34 | ✅ |
| Phase 8 | 35 | ✅ (97%) |
| Phase 9 | 17 | ✅ (100%) |
| Phase 10 | 26 | ✅ (100%) |
| **Total** | **162** | **100%** |

---

## Changelog

### January 23, 2026 - Phase 10 (Bulk Operations & Kanban)
- **Kanban Board View**:
  - 4 columns: To Do, In Progress, Completed, Cancelled
  - Drag-and-drop to change task status (all users)
  - Compact task cards with priority indicator, title, assignee, due date
  - View toggle button (List ↔ Kanban)
- **Bulk Operations (Admin/Manager only)**:
  - Bulk Edit: Update status, priority, or reassign multiple tasks
  - Bulk Cancel: Soft delete (set status to "cancelled")
  - Bulk Delete: Permanent deletion with comments/attachments cleanup
  - Checkbox selection with Select All / Deselect All
  - Bulk action bar with Edit, Cancel, Delete buttons
- **New API Endpoints**:
  - `POST /api/tasks/bulk/update`
  - `POST /api/tasks/bulk/cancel`
  - `DELETE /api/tasks/bulk/delete`

### January 23, 2026 - Phase 9 (Bug Fix)
- Fixed "Failed to fetch task details" error when viewing tasks not assigned to user
- Root cause: Authorization restrictions on comments/attachments conflicted with "all tasks visible" feature
- Updated comments.py: All authenticated users can now view and add comments on any task
- Updated attachments.py: All authenticated users can now view attachments on any task
- Fixed case-insensitive title sorting using MongoDB collation

### January 23, 2026 - Phase 8
- All users can now see ALL tasks (removed role-based restrictions)
- Task search: by title and description (case-insensitive)
- Task filters: status, priority, assigned_to, due date range, overdue only
- Task sorting: 5 fields with asc/desc order
- Task stats summary endpoint
- Pagination support
- Frontend: Search bar, expandable filters panel, stats cards

### January 22, 2026 - Phase 7
- Added roles: sales, operations, marketing, accounts
- Chat: Pin conversations and messages
- Chat: Search messages across conversations

### Previous
- Phase 6: Chat system with WebSocket
- Phase 5: User Management, Notification Sound
- Phase 1-4: Foundation, Comments, Attachments, Reports, Notifications
