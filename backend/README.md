# TripStars Task Management System - Backend

## Architecture

Production-ready FastAPI backend with MongoDB using best practices:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # Shared dependencies (auth, etc.)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── users.py       # User management
│   │       ├── tasks.py       # Task management
│   │       └── comments.py    # Comments (PHASE 2)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings and configuration
│   │   └── security.py        # JWT, password hashing
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py         # MongoDB connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # User document model
│   │   ├── task.py            # Task document model
│   │   └── comment.py         # Comment document model
│   └── schemas/
│       ├── __init__.py
│       ├── auth.py            # Auth request/response schemas
│       ├── user.py            # User Pydantic schemas
│       ├── task.py            # Task Pydantic schemas
│       └── comment.py         # Comment Pydantic schemas
├── requirements.txt
├── .env.example
└── README.md
```

## Database Schema (MongoDB)

### Collections

#### 1. users
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "hashed_password": "bcrypt_hash",
  "role": "admin|manager|team_member",
  "is_active": true,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### 2. tasks
```json
{
  "id": "uuid",
  "title": "Task title",
  "description": "Task description",
  "priority": "low|medium|high",
  "status": "todo|in_progress|completed",
  "assigned_to": "user_id",
  "assigned_to_email": "user@example.com",
  "assigned_to_name": "John Doe",
  "created_by": "user_id",
  "created_by_name": "Manager Name",
  "due_date": "2024-12-31",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### 3. comments
```json
{
  "id": "uuid",
  "task_id": "task_uuid",
  "user_id": "user_uuid",
  "user_name": "John Doe",
  "user_email": "user@example.com",
  "content": "Comment text",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

## API Documentation

### Authentication

**POST** `/api/auth/login`
- Login with email and password
- Returns JWT token and user data
```json
{
  "email": "admin@tripstars.com",
  "password": "Admin@123"
}
```

**GET** `/api/auth/me`
- Get current user info (requires JWT)

### Users

**POST** `/api/users` (Admin only)
- Create new user
```json
{
  "email": "user@tripstars.com",
  "full_name": "User Name",
  "password": "SecurePass123",
  "role": "team_member"
}
```

**GET** `/api/users` (Admin, Manager)
- List all users

**GET** `/api/users/{user_id}` (Admin, Manager)
- Get user by ID

### Tasks

**POST** `/api/tasks` (Admin, Manager)
- Create new task
```json
{
  "title": "Task Title",
  "description": "Task description",
  "priority": "high",
  "assigned_to": "user_id",
  "due_date": "2024-12-31"
}
```

**GET** `/api/tasks`
- List tasks (filtered by role)

**GET** `/api/tasks/{task_id}`
- Get task by ID

**PATCH** `/api/tasks/{task_id}`
- Update task
- Team members can only update status
- Managers/Admins can update all fields

**DELETE** `/api/tasks/{task_id}` (Admin, Manager)
- Delete task

### Comments (PHASE 2)

**POST** `/api/comments`
- Create comment on task
```json
{
  "task_id": "task_uuid",
  "content": "Comment text"
}
```

**GET** `/api/comments/task/{task_id}`
- List all comments for a task

**GET** `/api/comments/{comment_id}`
- Get comment by ID

**PATCH** `/api/comments/{comment_id}`
- Update comment (author only)

**DELETE** `/api/comments/{comment_id}`
- Delete comment (author or admin)

### Stats

**GET** `/api/stats`
- Get task statistics (todo, in_progress, completed counts)

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGO_URL=mongodb://localhost:27017
# For MongoDB Atlas:
# MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net

DB_NAME=tripstars_db
JWT_SECRET_KEY=your-super-secret-key-change-this
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 3. MongoDB Atlas Setup (Production)

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (free tier available)
3. Create a database user
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get connection string from "Connect" -> "Connect your application"
6. Update `MONGO_URL` in `.env`

### 4. Run the Application

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

API will be available at:
- API: http://localhost:8001/api
- Docs: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

### 5. Seed Users

Seed users are automatically created on startup:

- **Admin**: admin@tripstars.com / Admin@123
- **Manager**: manager@tripstars.com / Manager@123
- **Team Member**: member@tripstars.com / Member@123

## Role-Based Access Control

### Admin
- Create users
- Assign roles
- Full access to all tasks
- View all comments

### Manager
- Create and assign tasks
- Update all task fields
- View all tasks
- Comment on all tasks

### Team Member
- View assigned tasks only
- Update status of own tasks
- Comment on assigned tasks

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT authentication
- ✅ Role-based access control
- ✅ Environment variable configuration
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ MongoDB ObjectId handling

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Render.com / Railway / Heroku

1. Set environment variables in dashboard
2. Connect MongoDB Atlas
3. Deploy from Git repository

### AWS EC2

1. Install Python 3.11+
2. Install dependencies
3. Use Gunicorn/Uvicorn with systemd
4. Setup nginx as reverse proxy

## Testing

Test the API:

```bash
# Health check
curl http://localhost:8001/api/health

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tripstars.com","password":"Admin@123"}'

# Use token for authenticated requests
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## WebSocket Ready

The architecture supports WebSocket implementation:

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Real-time updates implementation
```

## Production Checklist

- [ ] Change `JWT_SECRET_KEY` to strong random string
- [ ] Use MongoDB Atlas or managed database
- [ ] Set `DEBUG=False`
- [ ] Configure proper CORS origins
- [ ] Setup HTTPS/SSL
- [ ] Enable database backups
- [ ] Setup monitoring (Sentry, DataDog, etc.)
- [ ] Configure rate limiting
- [ ] Add logging and error tracking
