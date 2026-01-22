# TripStars Task Management System - Product Requirements Document

## Overview
TripStars is an internal Task Management System for a travel company, built to manage tasks, assignments, reporting, and collaboration across teams.

**Tech Stack**: FastAPI (Python) + React + MongoDB

---

## User Personas & Roles

### Admin
- Full system access
- User management (CRUD)
- Task management for all users
- View all reports and audit logs
- System configuration

### Manager  
- Task management (create, assign, update)
- View all tasks and reports
- Cannot manage users
- Can cancel tasks

### Team Member
- View and update assigned tasks only
- Add comments and attachments
- Cannot create/assign tasks
- Cannot access user management

---

## Core Features

### Phase 1: Foundation (COMPLETE)
- [x] User authentication with JWT
- [x] Role-based access control (Admin, Manager, Team Member)
- [x] Basic task CRUD operations
- [x] MongoDB database integration

### Phase 2: Collaboration (COMPLETE)
- [x] Comments system on tasks
- [x] Modular backend architecture
- [x] Task status workflow (todo → in_progress → completed)

### Phase 3: Attachments & Reporting (COMPLETE)
- [x] File attachments on tasks
- [x] Productivity reports dashboard
- [x] User task statistics

### Phase 4: Notifications & Automation (COMPLETE)
- [x] In-app notifications
- [x] Email notifications (task assignments, due dates)
- [x] Background scheduler for overdue task checks
- [x] Audit logging for important actions

### Phase 5: Production Hardening (COMPLETE - Jan 22, 2026)
- [x] **User Management Frontend** - Full CRUD UI for admins
  - Create, edit, reset password, activate/deactivate users
  - Navigation link and route integrated
- [x] **Task Assignment UX** - User dropdown instead of roles
  - Fetches actual users from /api/users
  - Shows name and email for identification
- [x] **Notification Sound System**
  - Audio notification on new notifications
  - Toggle button to enable/disable
  - Persists preference in localStorage
- [x] **Cancelled Task Status**
  - New "cancelled" status in task lifecycle
  - Task deletion disabled (returns 405)
  - Dedicated cancel endpoint
- [x] **Enhanced Audit Logging**
  - Task reassignment logging with old/new assignee
  - User lifecycle events (create, update, deactivate, activate)
- [x] **Access/Refresh Tokens** - Production-grade auth

---

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Login with email/password |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/logout` | POST | Logout and revoke tokens |
| `/api/auth/me` | GET | Get current user |

### Users (Admin/Manager read, Admin write)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | GET | List all users |
| `/api/users` | POST | Create user (Admin) |
| `/api/users/{id}` | GET | Get user by ID |
| `/api/users/{id}` | PATCH | Update user (Admin) |
| `/api/users/{id}/reset-password` | POST | Reset password (Admin) |
| `/api/users/{id}/deactivate` | POST | Deactivate user (Admin) |
| `/api/users/{id}/activate` | POST | Activate user (Admin) |

### Tasks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List tasks (filtered by role) |
| `/api/tasks` | POST | Create task |
| `/api/tasks/{id}` | GET | Get task details |
| `/api/tasks/{id}` | PATCH | Update task |
| `/api/tasks/{id}` | DELETE | **DISABLED** (returns 405) |
| `/api/tasks/{id}/cancel` | PATCH | Cancel task |

### Comments & Attachments
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/comments` | POST | Add comment |
| `/api/comments/task/{id}` | GET | Get task comments |
| `/api/attachments` | POST | Upload attachment |
| `/api/attachments/task/{id}` | GET | Get task attachments |
| `/api/attachments/{id}/download` | GET | Download attachment |

### Reports & Notifications
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/reports/user-productivity` | GET | Get productivity stats |
| `/api/notifications` | GET | Get user notifications |
| `/api/notifications/unread-count` | GET | Get unread count |
| `/api/notifications/mark-read/{id}` | POST | Mark notification read |
| `/api/notifications/mark-all-read` | POST | Mark all read |
| `/api/audit-logs` | GET | Get audit logs (Admin/Manager) |

---

## Database Collections

- `users` - User accounts and roles
- `tasks` - Task data with assignments
- `comments` - Task comments
- `attachments` - File attachment metadata
- `notifications` - User notifications
- `audit_logs` - Action audit trail
- `refresh_tokens` - Token storage for auth

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tripstars.com | Admin@123 |
| Manager | manager@tripstars.com | Manager@123 |
| Team Member | member@tripstars.com | Member@123 |

---

## File Structure

```
/app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── routes/ (auth, tasks, users, comments, attachments, reports, notifications, audit_logs)
│   │   ├── core/ (config, security)
│   │   ├── db/ (mongodb)
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/ (email, scheduler, audit, notification)
│   ├── tests/
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/ (Layout, NotificationBell)
    │   ├── contexts/ (AuthContext)
    │   └── pages/ (Dashboard, TaskList, TaskDetail, UserManagement, Reports, AuditLogs)
    └── package.json
```

---

## Prioritized Backlog

### P0 (Must Have) - COMPLETE
All core features implemented

### P1 (Should Have) - Future Enhancements
- [ ] Task search and filtering
- [ ] Bulk task operations
- [ ] Task dependencies
- [ ] Export reports to PDF/CSV

### P2 (Nice to Have)
- [ ] Dark mode theme
- [ ] Mobile-responsive improvements
- [ ] Task templates
- [ ] Integration with calendar apps

---

## Testing Status

| Phase | Backend | Frontend | Status |
|-------|---------|----------|--------|
| Phase 1 | ✅ | ✅ | Complete |
| Phase 2 | ✅ | ✅ | Complete |
| Phase 3 | ✅ | ✅ | Complete |
| Phase 4 | ✅ | ✅ | Complete |
| Phase 5 | ✅ (23/23 tests) | ✅ | Complete |

---

## Changelog

### January 22, 2026 - Phase 5 Complete
- Added User Management CRUD frontend for admins
- Implemented task assignment with user dropdown
- Added notification sound with toggle
- Disabled task deletion (returns 405)
- Added cancelled task status
- Enhanced audit logging for reassignments
- Created comprehensive test suite (23 tests)

### Previous Phases
- Phase 4: Notifications, scheduler, audit logs
- Phase 3: Attachments, reports, dashboard
- Phase 2: Comments, modular architecture
- Phase 1: Auth, tasks, users foundation
