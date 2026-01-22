# TripStars Task Management System - Product Requirements Document

## Overview
TripStars is an internal Task Management System for a travel company, built to manage tasks, assignments, reporting, collaboration, and real-time communication across teams.

**Tech Stack**: FastAPI (Python) + React + MongoDB (Atlas compatible) + WebSocket

---

## User Personas & Roles

### Admin
- Full system access
- User management (CRUD for all roles)
- Task management for all users
- View all reports and audit logs
- Cannot deactivate own account

### Manager  
- Task management (create, assign, update)
- View all tasks and reports
- Cannot manage users
- Can cancel tasks
- Create group chats

### Sales / Operations / Marketing / Accounts
- Create tasks and assign to other staff (not admins)
- Add comments and attachments to tasks
- Participate in one-to-one and group chats
- Receive notifications
- Cannot manage users, reports, or audit logs

### Team Member (Legacy)
- Same permissions as Sales/Operations/Marketing/Accounts
- Maintained for backward compatibility

---

## Core Features

### Phase 1-5: Foundation through Production Hardening (COMPLETE)
- User authentication with JWT + Refresh tokens
- Role-based access control
- Task CRUD with comments and attachments
- Productivity reports and dashboards
- Notifications (in-app + email)
- Background scheduler
- Audit logging
- User Management CRUD frontend

### Phase 6: Chat System (COMPLETE)
- Direct Messages (1-on-1)
- Group Chats (everyone can create)
- File attachments (PDF, JPG, PNG, DOC, DOCX - 10MB)
- Read receipts (✓ delivered, ✓✓ read)
- Typing indicators
- Real-time WebSocket delivery

### Phase 7: Extended Roles & Chat Enhancements (COMPLETE - Jan 22, 2026)
- **New Roles Added**
  - Sales, Operations, Marketing, Accounts
  - Same capabilities as team_member
  - Cannot assign tasks to admins
  - Cannot access reports/audit (except own stats)

- **Chat Pin Feature**
  - Pin/unpin conversations (per user)
  - Pin/unpin messages
  - Pinned conversations appear first
  - View pinned messages in conversation

- **Chat Search Feature**
  - Search across all conversations
  - Search within specific conversation
  - Results show conversation name and sender

- **Security Fixes**
  - Admin cannot deactivate self
  - Reports restricted for staff roles (own stats only)

---

## API Endpoints

### Authentication
| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/auth/login` | POST | Public | Login |
| `/api/auth/refresh` | POST | Public | Refresh token |
| `/api/auth/logout` | POST | Auth | Logout |
| `/api/auth/me` | GET | Auth | Get current user |

### Users
| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/users/assignable` | GET | All Staff | Users for task assignment |
| `/api/users` | GET | Admin/Manager | List all users |
| `/api/users` | POST | Admin | Create user |
| `/api/users/{id}` | PATCH | Admin | Update user |
| `/api/users/{id}/deactivate` | POST | Admin | Deactivate (not self) |
| `/api/users/{id}/activate` | POST | Admin | Activate user |

### Tasks
| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/tasks` | GET | All Staff | List tasks |
| `/api/tasks` | POST | All Staff | Create task |
| `/api/tasks/{id}` | PATCH | All Staff | Update task |
| `/api/tasks/{id}` | DELETE | - | **DISABLED** (405) |
| `/api/tasks/{id}/cancel` | PATCH | All Staff | Cancel task |

### Chat
| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/chat/conversations` | GET | All Staff | List conversations |
| `/api/chat/conversations` | POST | All Staff | Create DM/Group |
| `/api/chat/conversations/{id}/messages` | GET | Participants | Get messages |
| `/api/chat/conversations/{id}/messages` | POST | Participants | Send message |
| `/api/chat/conversations/{id}/pin` | POST | Participants | Pin/unpin conversation |
| `/api/chat/conversations/{id}/messages/{mid}/pin` | POST | Participants | Pin/unpin message |
| `/api/chat/conversations/{id}/pinned-messages` | GET | Participants | Get pinned messages |
| `/api/chat/search` | GET | All Staff | Search messages |
| `/api/chat/conversations/{id}/attachments` | POST | Participants | Upload attachment |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/api/ws?token=<token>` | Real-time notifications & chat |

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

## Database Collections

| Collection | Description |
|------------|-------------|
| `users` | User accounts with roles |
| `tasks` | Task data |
| `comments` | Task comments |
| `attachments` | Task attachments |
| `notifications` | User notifications |
| `audit_logs` | Action audit trail |
| `refresh_tokens` | Auth tokens |
| `conversations` | Chat conversations (pinned_by field) |
| `messages` | Chat messages (is_pinned, pinned_by, pinned_at) |
| `chat_attachments` | Chat file attachments |

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
| **Total** | **84** | **100%** |

---

## Changelog

### January 22, 2026 - Phase 7
- Added roles: sales, operations, marketing, accounts
- Chat: Pin conversations and messages
- Chat: Search messages across conversations
- Admin cannot deactivate self
- Reports restricted for staff roles
- Created DEPLOYMENT_GUIDE.md for PM2+Nginx+MongoDB Atlas

### Previous
- Phase 6: Chat system with WebSocket
- Phase 5: User Management, Notification Sound
- Phase 4: Notifications, scheduler, audit logs
- Phase 3: Attachments, reports, dashboard
- Phase 2: Comments, modular architecture
- Phase 1: Auth, tasks, users foundation
