# Task Tracker - Backend Setup Guide

## ✅ What's Been Set Up

- ✅ `.env` file with MongoDB Atlas configuration
- ✅ `.env.example` file for reference
- ✅ `Dockerfile` for containerized backend
- ✅ `docker-compose.yml` for easy orchestration
- ✅ Updated `requirements.txt` with compatible dependencies
- ✅ Fixed backend code configuration
- ✅ Startup scripts for Windows and Linux/Mac

---

## 🚀 Quick Start (Recommended)

### Windows Users:
```bash
# Simply double-click or run:
START_BACKEND.bat
```

### Linux/Mac Users:
```bash
# Make script executable
chmod +x START_BACKEND.sh

# Run the startup script
./START_BACKEND.sh
```

### Manual Docker Command:
```bash
docker-compose up --build
```

---

## 📍 Access Points

Once the backend is running:

| Service | URL |
|---------|-----|
| **API** | `http://localhost:8001/api` |
| **Swagger Docs** | `http://localhost:8001/api/docs` |
| **ReDoc** | `http://localhost:8001/api/redoc` |

---

## 🔐 Test Credentials

The system automatically creates these users:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tripstars.com | Admin@123 |
| Manager | manager@tripstars.com | Manager@123 |
| Team Member | member@tripstars.com | Member@123 |

---

## 🗄️ Database Configuration

**Current Setup:** MongoDB Atlas (Cloud)
- **Host:** cluster0.fqy0kzg.mongodb.net
- **Database:** task_tracker
- **Connection String:** Located in `.env`

### To Use Local MongoDB Instead:

1. Uncomment the MongoDB service in `docker-compose.yml`:

```yaml
  mongodb:
    image: mongo:7.0
    container_name: task-tracker-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db
    networks:
      - app-network
```

2. Update `.env` to use local MongoDB:
```env
MONGO_URL=mongodb://admin:password@mongodb:27017/
```

3. Uncomment the `mongodb_data` volume at the end

---

## 📋 Project Structure

```
backend/
├── Dockerfile              # Container configuration
├── .dockerignore           # Docker build ignore patterns
├── .env                    # Environment variables (NOT in git)
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── core/
│   │   ├── config.py      # Configuration settings
│   │   └── security.py    # JWT & password hashing
│   ├── api/
│   │   └── routes/        # API endpoints
│   ├── db/
│   │   └── mongodb.py     # Database connection
│   ├── models/            # MongoDB models
│   └── services/          # Business logic
```

---

## 🛠️ Environment Variables

All variables are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URL` | MongoDB Atlas | Database connection string |
| `DB_NAME` | task_tracker | Database name |
| `JWT_SECRET_KEY` | (set in .env) | Secret key for JWT tokens |
| `CORS_ORIGINS` | localhost:3000,5173 | Allowed frontend origins |
| `DEBUG` | False | Debug mode (never enable in production) |
| `UPLOAD_DIR` | ./uploads | File upload directory |

---

## 🐳 Docker Commands

### Start Services
```bash
docker-compose up --build
```

### Run in Background
```bash
docker-compose up -d --build
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f backend
```

### Access Backend Container Shell
```bash
docker exec -it task-tracker-backend bash
```

---

## 🧪 Testing the API

### Using cURL:

```bash
# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tripstars.com","password":"Admin@123"}'

# Get current user (use token from login response)
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Swagger UI:
1. Open `http://localhost:8001/api/docs`
2. Click **Authorize** button
3. Login with test credentials
4. Try API endpoints

---

## 🐛 Troubleshooting

### Error: "Could not import module 'main'"
- ✅ **Fixed!** We now use `app.main:app` (correct path)
- Dockerfile and docker-compose.yml use the correct command

### Error: "Docker is not running"
- Install and start Docker Desktop
- Make sure Docker daemon is running

### MongoDB Connection Timeout
- Check internet connection (if using MongoDB Atlas)
- Verify MongoDB Atlas cluster is active
- Check IP whitelist in MongoDB Atlas console

### Port Already in Use
- Change port in `docker-compose.yml`
- Or stop other containers: `docker-compose down`

---

## 📚 API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user info

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Users
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user

See Swagger docs for complete API reference.

---

## ✨ Next Steps

1. **Start the backend** using `START_BACKEND.bat` (Windows) or `./START_BACKEND.sh` (Linux/Mac)
2. **Visit** `http://localhost:8001/api/docs`
3. **Login** with admin credentials
4. **Explore** the API endpoints
5. **Connect** your frontend to the backend

---

## 🔒 Security Notes

- ⚠️ Change `JWT_SECRET_KEY` in `.env` for production
- ⚠️ Use strong passwords for MongoDB Atlas
- ⚠️ Never commit `.env` file (already in `.gitignore`)
- ⚠️ Set `DEBUG=False` in production
- ⚠️ Configure proper CORS origins for your domain

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify `.env` has correct MongoDB credentials
3. Ensure Docker Desktop is running
4. Check that port 8001 is not in use

---

**Happy coding! 🚀**
