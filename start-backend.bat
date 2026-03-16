@echo off
REM Start Backend Server
REM This script runs the FastAPI backend on port 8001

cd backend

echo Installing/updating backend dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI backend on http://localhost:8001
echo API docs available at http://localhost:8001/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
