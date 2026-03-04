@echo off
REM Windows Batch Script to start Task Tracker Backend

echo.
echo ========================================
echo Task Tracker Backend - Docker Startup
echo ========================================

REM Check if Docker is installed and running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not installed.
    echo Please install Docker Desktop and ensure it's running.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Docker is running
echo.
echo Building and starting services...
echo.

REM Build and start services
docker-compose up --build

echo.
echo ========================================
echo Backend is starting!
echo ========================================
echo API URL: http://localhost:8001/api
echo API Docs: http://localhost:8001/api/docs
echo ReDoc: http://localhost:8001/api/redoc
echo.
echo Test Credentials:
echo   Admin: admin@tripstars.com / Admin@123
echo   Manager: manager@tripstars.com / Manager@123
echo   Member: member@tripstars.com / Member@123
echo ========================================
echo.
pause
