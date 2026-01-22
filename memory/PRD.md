# TripStars Task Management System - Product Requirements Document

## Overview
TripStars is an internal Task Management System for a travel company, built to manage tasks, assignments, reporting, collaboration, and real-time communication across teams.

**Tech Stack**: FastAPI (Python) + React + MongoDB + WebSocket

---

## User Personas & Roles

### Admin
- Full system access
- User management (CRUD)
- Task management for all users
- View all reports and audit logs
- Cannot deactivate own account

### Manager  
- Task management (create, assign, update)
- View all tasks and reports
- Cannot manage users
- Can cancel tasks
- Create group chats

### Team Member
- View and update assigned tasks
- **Can now create and assign tasks** to other members and managers (NOT admins)
- Add comments and attachments
- Access to All Tasks page
- Chat with all users
- Create group chats

---

## Core Features

### Phase 1-4: Foundation, Collaboration, Reporting, Notifications (COMPLETE)
- User authentication with JWT + Refresh tokens
- Role-based access control
- Task CRUD operations with comments and attachments
- Productivity reports and dashboards
- In-app and email notifications
- Background scheduler for overdue tasks
- Audit logging

### Phase 5: Production Hardening (COMPLETE)
- User Management CRUD frontend for admins
- Task assignment with user dropdown
- Notification sound with toggle
- Cancelled task status + delete prevention
- Enhanced audit logging

### Phase 6: Chat & Task Assignment Updates (COMPLETE - Jan 22, 2026)
- **Team Member Task Assignment**
  - Team members can create tasks
  - Can assign to managers and other team members
  - Cannot assign to admins (403 error)
  - New `/api/users/assignable` endpoint

- **Admin Self-Delete Prevention**
  - Admin cannot deactivate own account (400 error)

- **Real-time WebSocket Notifications**
  - WebSocket endpoint: `/api/ws?token=<access_token>`
  - Notifications pushed in real-time after saving to MongoDB
  - Sound plays on new notifications
  - Local cache prevents duplicate notifications

- **Chat System (Full Feature)**
  - Direct Messages (1-on-1)
  - Group Chats (everyone can create)
  - File attachments (PDF, JPG, PNG, DOC, DOCX - 10MB max)
  - Read receipts (✓ delivered, ✓✓ read)
  - Typing indicators
  - Real-time message delivery via WebSocket

---

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Login with email/password |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/logout` | POST | Logout and revoke tokens |
| `/api/auth/me` | GET | Get current user |

### Users
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/assignable` | GET | Get users assignable for tasks (role-filtered) |
| `/api/users` | GET | List all users (Admin/Manager) |
| `/api/users` | POST | Create user (Admin) |
| `/api/users/{id}` | GET | Get user by ID |
| `/api/users/{id}` | PATCH | Update user (Admin) |
| `/api/users/{id}/deactivate` | POST | Deactivate user (Admin, cannot self) |
| `/api/users/{id}/activate` | POST | Activate user (Admin) |

### Tasks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List tasks |
| `/api/tasks` | POST | Create task (all users) |
| `/api/tasks/{id}` | GET | Get task details |
| `/api/tasks/{id}` | PATCH | Update task |
| `/api/tasks/{id}` | DELETE | **DISABLED** (returns 405) |
| `/api/tasks/{id}/cancel` | PATCH | Cancel task |

### Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/conversations` | GET | List user's conversations |
| `/api/chat/conversations` | POST | Create DM or Group |
| `/api/chat/conversations/{id}` | GET | Get conversation details |
| `/api/chat/conversations/{id}` | PATCH | Update group (add/remove members) |
| `/api/chat/conversations/{id}/messages` | GET | Get messages |
| `/api/chat/conversations/{id}/messages` | POST | Send message |
| `/api/chat/conversations/{id}/read` | POST | Mark messages read |
| `/api/chat/conversations/{id}/typing` | POST | Send typing indicator |
| `/api/chat/conversations/{id}/attachments` | POST | Upload attachment |
| `/api/chat/attachments/{id}/download` | GET | Download attachment |
| `/api/chat/users/available` | GET | Get users for chat |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/api/ws?token=<token>` | Real-time connection for notifications & chat |

### Other Endpoints
- Comments, Attachments, Reports, Notifications, Audit Logs (see Phase 1-5)

---

## Database Collections

- `users` - User accounts and roles
- `tasks` - Task data with assignments
- `comments` - Task comments
- `attachments` - Task file attachments
- `notifications` - User notifications
- `audit_logs` - Action audit trail
- `refresh_tokens` - Token storage for auth
- `conversations` - Chat conversations (DM + Groups)
- `messages` - Chat messages
- `chat_attachments` - Chat file attachments

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
│   │   ├── api/routes/ (auth, tasks, users, chat, websocket, etc.)
│   │   ├── core/ (config, security)
│   │   ├── models/ (user, task, chat)
│   │   ├── schemas/ (user, task, chat)
│   │   ├── services/ (email, scheduler, notification, websocket_manager)
│   │   └── db/
│   ├── uploads/chat/ (chat attachments)
│   └── tests/
└── frontend/
    ├── src/
    │   ├── components/ (Layout, NotificationBell)
    │   ├── contexts/ (AuthContext, WebSocketContext)
    │   └── pages/ (Dashboard, TaskList, Chat, UserManagement, etc.)
    └── package.json
```

---

## Testing Status

| Phase | Backend | Frontend | Status |
|-------|---------|----------|--------|
| Phase 1-4 | ✅ | ✅ | Complete |
| Phase 5 | ✅ (23 tests) | ✅ | Complete |
| Phase 6 | ✅ (27 tests) | ✅ | Complete |

**Total: 50+ automated tests**

---

## Changelog

### January 22, 2026 - Phase 6 Complete
- Team members can now create tasks and assign to managers/members
- Admin cannot deactivate own account
- Real-time WebSocket notifications
- Full chat system with DM, Groups, Attachments, Read Receipts, Typing Indicators
- 27 new backend tests (100% pass rate)

### Previous Phases
- Phase 5: User Management, Notification Sound, Cancelled Status
- Phase 4: Notifications, scheduler, audit logs
- Phase 3: Attachments, reports, dashboard
- Phase 2: Comments, modular architecture
- Phase 1: Auth, tasks, users foundation

---

## Prioritized Backlog

### P1 (Should Have)
- [ ] Task search and filtering
- [ ] Bulk task operations
- [ ] Export reports to PDF/CSV

### P2 (Nice to Have)
- [ ] Dark mode theme
- [ ] Task dependencies
- [ ] Integration with calendar apps
- [ ] Push notifications (mobile)
