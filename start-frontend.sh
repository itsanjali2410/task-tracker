#!/bin/bash

# Start Frontend Server
# This script runs the React frontend on port 3000
# Make sure backend is running on port 8001 first!

cd frontend

# Install dependencies if needed
echo "Installing/updating frontend dependencies..."
npm install

# Set backend URL for development
export REACT_APP_BACKEND_URL=http://localhost:8001

# Start the dev server
echo "Starting React frontend on http://localhost:3000"
echo "Make sure the backend is running on http://localhost:8001"
npm start
