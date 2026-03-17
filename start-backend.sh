#!/bin/bash

# Start Backend Server
# This script runs the FastAPI backend on port 8001

cd backend

# Install dependencies if needed
echo "Installing/updating backend dependencies..."
pip install -r requirements.txt

# Start the server
echo "Starting FastAPI backend on http://localhost:8001"
echo "API docs available at http://localhost:8001/docs"
uvicorn src.app.main:app --host 0.0.0.0 --port 8001 --reload
