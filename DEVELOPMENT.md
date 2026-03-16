# Development Setup - Running Backend & Frontend Separately

This guide explains how to run the backend and frontend in separate terminals for development.

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **pip** (Python package manager)
- **npm** (Node package manager)
- MongoDB connection (ensure your MONGO_URL is accessible)

## Quick Start

### Windows Users

#### Terminal 1: Start Backend
```bash
# Double-click this file or run in Command Prompt/PowerShell
start-backend.bat
```

#### Terminal 2: Start Frontend
```bash
# Double-click this file or run in Command Prompt/PowerShell
start-frontend.bat
```

---

### macOS/Linux Users

#### Terminal 1: Start Backend
```bash
chmod +x start-backend.sh
./start-backend.sh
```

#### Terminal 2: Start Frontend
```bash
chmod +x start-frontend.sh
./start-frontend.sh
```

---

## Manual Setup (If scripts don't work)

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file or export)
export MONGO_URL=mongodb+srv://tripstars:trip1234@cluster0.fqy0kzg.mongodb.net/
export DB_NAME=task_tracker
export JWT_SECRET_KEY=tripstars-secret-key-change-in-production
export CORS_ORIGINS=http://localhost:3000,http://localhost:5173
export DEBUG=False

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: **http://localhost:8001**
API Documentation: **http://localhost:8001/docs**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set backend URL
export REACT_APP_BACKEND_URL=http://localhost:8001

# Start development server
npm start
```

Frontend will be available at: **http://localhost:3000**

---

## Environment Configuration

### Backend (.env file)

Create `backend/.env`:
```
MONGO_URL=mongodb+srv://tripstars:trip1234@cluster0.fqy0kzg.mongodb.net/
DB_NAME=task_tracker
JWT_SECRET_KEY=tripstars-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=False
```

### Frontend (.env file)

Create `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Port Configuration

- **Backend**: Port 8001 (http://localhost:8001)
- **Frontend**: Port 3000 (http://localhost:3000)

If you need to use different ports:

**Backend**: Edit `start-backend.sh` or `start-backend.bat`
```bash
# Change --port 8001 to your desired port
uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload
```

**Frontend**: Edit package.json scripts or set PORT env var
```bash
export PORT=3500
npm start
```

---

## Troubleshooting

### Backend won't start
- Check if port 8001 is already in use: `lsof -i :8001` (macOS/Linux)
- Verify MongoDB connection is accessible
- Check Python version: `python --version`
- Install dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Clear cache: `rm -rf node_modules package-lock.json && npm install`
- Check Node version: `node --version`
- Ensure backend URL is set correctly in `.env`

### CORS errors
- Verify `CORS_ORIGINS` includes `http://localhost:3000`
- Backend CORS_ORIGINS should be: `http://localhost:3000,http://localhost:5173`

### API calls failing
- Check backend is running on `http://localhost:8001`
- Verify `REACT_APP_BACKEND_URL=http://localhost:8001` in frontend
- Check browser console for actual error messages

---

## Development Workflow

1. **Start Backend Terminal**: Run `start-backend.bat` or `./start-backend.sh`
   - Backend will auto-reload on file changes
   - API docs at http://localhost:8001/docs

2. **Start Frontend Terminal**: Run `start-frontend.bat` or `./start-frontend.sh`
   - Frontend will auto-reload on file changes
   - Access app at http://localhost:3000

3. **Make Changes**:
   - Backend changes auto-reload in terminal 1
   - Frontend changes auto-reload in browser

4. **View Logs**: Both terminals show real-time output

---

## Using Docker (Alternative)

If you prefer Docker:

```bash
# Build and start both services
docker compose up --build

# Or just one service
docker compose up backend
docker compose up frontend
```

---

## Tips

- **Backend API Docs**: http://localhost:8001/docs (Interactive Swagger UI)
- **Debugging**: Use `print()` in backend code, check terminal output
- **React DevTools**: Install React DevTools browser extension for frontend debugging
- **Network Requests**: Check browser DevTools Network tab for API calls
- **Terminal Output**: Keep both terminals visible to monitor logs

---

## Git & Commits

After making changes:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

---

For more info, see README.md in the root directory.
