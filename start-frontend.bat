@echo off
REM Start Frontend Server
REM This script runs the React frontend on port 3000
REM Make sure backend is running on port 8001 first!

cd frontend

echo Installing/updating frontend dependencies...
call npm install

REM Set backend URL for development
set REACT_APP_BACKEND_URL=http://localhost:8001

echo.
echo Starting React frontend on http://localhost:3000
echo Make sure the backend is running on http://localhost:8001
echo.
call npm start

pause
