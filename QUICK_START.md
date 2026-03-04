# 🚀 Quick Start Guide

## ⚡ 30-Second Setup

### Option 1: Everything with Docker (Recommended)
```bash
docker-compose up --build
```
Then open: `http://localhost:3000`

### Option 2: Frontend Only (Production Backend)
```bash
cd frontend
npm install
npm start
```
Then open: `http://localhost:3000`

### Option 3: Backend Only
```bash
cd backend
START_BACKEND.bat  # Windows
# or
./START_BACKEND.sh # Linux/Mac
```
Then visit: `http://localhost:8001/api/docs`

---

## 📍 Where to Go

| What | Where |
|------|-------|
| **Web App** | http://localhost:3000 |
| **API Docs** | http://localhost:8001/api/docs |
| **Production Backend** | https://task-tracker-production-2750.up.railway.app |

---

## 🔐 Login Credentials

```
Admin:     admin@tripstars.com / Admin@123
Manager:   manager@tripstars.com / Manager@123
Member:    member@tripstars.com / Member@123
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `frontend/.env` | Frontend configuration (backend URL) |
| `backend/.env` | Backend configuration (MongoDB, JWT) |
| `docker-compose.yml` | Run everything in Docker |
| `.env.example` files | Templates for team |
| `src/config/api.js` | Frontend API configuration |

---

## 🔄 Switch Backend URL

Edit `frontend/.env`:

```env
# Production (Current)
REACT_APP_BACKEND_URL=https://task-tracker-production-2750.up.railway.app

# Local Development
REACT_APP_BACKEND_URL=http://localhost:8001

# Docker
REACT_APP_BACKEND_URL=http://backend:8001
```

Then restart the frontend.

---

## ✅ Status

- ✅ Frontend configured for production backend
- ✅ Environment variables set up
- ✅ Docker ready
- ✅ All documentation complete
- ✅ Ready to deploy

---

## 🎯 What You Can Do Now

1. **Run the app:**
   ```bash
   docker-compose up --build
   ```

2. **Access the app:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8001/api/docs

3. **Login:** Use test credentials above

4. **Start building:** The backend and frontend are connected!

---

**Need help?**
- See `ENVIRONMENT_SETUP_COMPLETE.md` for detailed info
- See `SETUP_GUIDE.md` for backend details
- See `FRONTEND_ENV_SETUP.md` for frontend details

**Let's go! 🚀**
