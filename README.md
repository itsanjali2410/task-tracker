# TripStars Task Management System

**Production-ready full-stack task management application for travel companies**

## Overview

TripStars is a comprehensive task management system designed specifically for travel companies. It features role-based access control, task assignment, status tracking, and team collaboration through comments.

## Tech Stack

### Backend
- **FastAPI** (Python) - Modern, fast web framework
- **MongoDB** - NoSQL database with Motor (async driver)
- **JWT** - Secure authentication
- **Pydantic** - Data validation
- **Bcrypt** - Password hashing

### Frontend
- **React** - Component-based UI
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first styling
- **Sonner** - Toast notifications

## Features

### Phase 1: Core Functionality
- ✅ User authentication (email + password)
- ✅ JWT token-based authorization
- ✅ Role-based access control (Admin, Manager, Team Member)
- ✅ User management (create, list, view)
- ✅ Task management (create, assign, update, delete)
- ✅ Task status tracking (To Do, In Progress, Completed)
- ✅ Priority levels (Low, Medium, High)
- ✅ Dashboard with statistics
- ✅ Due date tracking

### Phase 2: Collaboration
- ✅ Task comments system
- ✅ Real-time comment threads
- ✅ Task detail view
- ✅ Comment timestamps
- ✅ User attribution for comments

### Phase 3: Attachments & Productivity (NEW!)
- ✅ File attachments on tasks (PDF, JPG, PNG, DOC, DOCX)
- ✅ Secure file upload/download with 10MB limit
- ✅ Productivity tracking & scoring (0-100)
- ✅ User performance metrics (completion rate, on-time delivery, overdue)
- ✅ Team productivity reports (Managers/Admins only)
- ✅ Enhanced dashboards with productivity insights
- ✅ Individual and team-wide analytics

**📄 See [PHASE3_README.md](PHASE3_README.md) for detailed Phase 3 documentation**

## Project Structure

```
tripstars-task-management/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Config & security
│   │   ├── db/          # Database connection
│   │   ├── models/      # Data models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── main.py      # App entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/  # Reusable components
│   │   ├── contexts/    # React contexts
│   │   ├── pages/       # Page components
│   │   └── App.js       # Main app
│   ├── package.json
│   ├── .env.example
│   └── README.md
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB connection string

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at http://localhost:8001
- API Docs: http://localhost:8001/api/docs

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install
# or npm install

# Configure environment
cp .env.example .env
# Edit .env with backend URL

# Run development server
yarn start
# or npm start
```

Frontend will be available at http://localhost:3000

### 3. MongoDB Setup

#### Option A: Local MongoDB
```bash
# Install MongoDB
# macOS
brew install mongodb-community

# Ubuntu
sudo apt-get install mongodb

# Start MongoDB
mongod
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Create database user
4. Whitelist IP address
5. Get connection string
6. Update `MONGO_URL` in backend/.env

## Seed Data

The application automatically seeds three users on startup:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tripstars.com | Admin@123 |
| Manager | manager@tripstars.com | Manager@123 |
| Team Member | member@tripstars.com | Member@123 |

## Role Permissions

### Admin
- ✅ Create and manage users
- ✅ Assign roles
- ✅ Full access to all tasks
- ✅ View and manage all comments
- ✅ Delete tasks and comments

### Manager
- ✅ Create and assign tasks
- ✅ Update all task fields
- ✅ View all tasks
- ✅ Comment on all tasks
- ❌ Cannot create users

### Team Member
- ✅ View assigned tasks
- ✅ Update status of own tasks
- ✅ Comment on assigned tasks
- ❌ Cannot create or assign tasks
- ❌ Cannot view other users' tasks

## API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

### Key Endpoints

#### Authentication
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

#### Users
- `POST /api/users` - Create user (Admin)
- `GET /api/users` - List users (Admin, Manager)
- `GET /api/users/{id}` - Get user (Admin, Manager)

#### Tasks
- `POST /api/tasks` - Create task (Manager, Admin)
- `GET /api/tasks` - List tasks (filtered by role)
- `GET /api/tasks/{id}` - Get task details
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task (Manager, Admin)

#### Comments
- `POST /api/comments` - Add comment
- `GET /api/comments/task/{task_id}` - Get task comments
- `PATCH /api/comments/{id}` - Update comment (author)
- `DELETE /api/comments/{id}` - Delete comment (author, admin)

#### Attachments (Phase 3)
- `POST /api/attachments?task_id={id}` - Upload file to task
- `GET /api/attachments/task/{task_id}` - List task attachments
- `GET /api/attachments/{id}/download` - Download attachment
- `DELETE /api/attachments/{id}` - Delete attachment (uploader, admin)

#### Reports (Phase 3)
- `GET /api/reports/user-productivity` - Get user productivity metrics
- `GET /api/reports/team-overview` - Get team-wide analytics (Manager, Admin)

#### Stats
- `GET /api/stats` - Get task statistics

## Database Schema

### Collections

#### users
```javascript
{
  id: String,
  email: String,
  full_name: String,
  hashed_password: String,
  role: String, // 'admin', 'manager', 'team_member'
  is_active: Boolean,
  created_at: DateTime,
  updated_at: DateTime
}
```

#### tasks
```javascript
{
  id: String,
  title: String,
  description: String,
  priority: String, // 'low', 'medium', 'high'
  status: String, // 'todo', 'in_progress', 'completed'
  assigned_to: String, // user_id
  assigned_to_email: String,
  assigned_to_name: String,
  created_by: String, // user_id
  created_by_name: String,
  due_date: String,
  completed_at: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

#### comments
```javascript
{
  id: String,
  task_id: String,
  user_id: String,
  user_name: String,
  user_email: String,
  content: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

## Deployment

### Backend Deployment

#### Option 1: Render / Railway / Heroku
1. Connect GitHub repository
2. Set environment variables
3. Deploy

#### Option 2: AWS EC2
1. Setup EC2 instance
2. Install Python and dependencies
3. Configure nginx
4. Use systemd for process management

#### Option 3: Docker
```bash
cd backend
docker build -t tripstars-backend .
docker run -p 8001:8001 -e MONGO_URL="your_url" tripstars-backend
```

### Frontend Deployment

#### Option 1: Vercel (Recommended)
1. Connect GitHub repository
2. Set `REACT_APP_BACKEND_URL`
3. Deploy automatically

#### Option 2: Netlify
1. Build: `yarn build`
2. Deploy `build/` directory
3. Configure environment variables

#### Option 3: AWS S3 + CloudFront
1. Build: `yarn build`
2. Upload to S3
3. Configure CloudFront

## Security Considerations

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens for authentication
- ✅ Role-based access control
- ✅ Input validation with Pydantic
- ✅ CORS configuration
- ✅ Environment variables for secrets
- ✅ MongoDB ObjectId handling
- ✅ HTTPS recommended for production

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
yarn test
```

### Code Formatting
```bash
# Backend
black app/
isort app/

# Frontend
prettier --write src/
```

### Linting
```bash
# Backend
flake8 app/
mypy app/

# Frontend
eslint src/
```

## Production Checklist

### Backend
- [ ] Strong `JWT_SECRET_KEY`
- [ ] MongoDB Atlas or managed database
- [ ] `DEBUG=False`
- [ ] Proper CORS origins
- [ ] HTTPS enabled
- [ ] Error tracking (Sentry)
- [ ] Logging configured
- [ ] Rate limiting
- [ ] Database backups

### Frontend
- [ ] Production `REACT_APP_BACKEND_URL`
- [ ] HTTPS enabled
- [ ] CDN for static assets
- [ ] Error tracking
- [ ] Analytics
- [ ] Mobile testing
- [ ] Browser compatibility
- [ ] Performance optimization

## Future Enhancements

- [ ] Email notifications
- [ ] File attachments
- [ ] Task templates
- [ ] Advanced filtering
- [ ] Task dependencies
- [ ] Time tracking
- [ ] Reporting dashboard
- [ ] WebSocket for real-time updates
- [ ] Mobile app
- [ ] Bulk operations

## Support

For issues and questions:
- Backend: See `backend/README.md`
- Frontend: See `frontend/README.md`
- API Docs: http://localhost:8001/api/docs

## License

MIT License - See LICENSE file for details

## Contributors

Built with ❤️ for TripStars
