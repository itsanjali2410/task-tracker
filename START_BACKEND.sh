#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Task Tracker Backend - Docker Startup${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Build and start services
echo -e "\n${BLUE}Building and starting services...${NC}"
docker-compose up --build

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Backend is starting!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "📍 API URL: http://localhost:8001/api"
echo -e "📚 API Docs: http://localhost:8001/api/docs"
echo -e "📖 ReDoc: http://localhost:8001/api/redoc"
echo -e "\n${GREEN}Test Credentials:${NC}"
echo -e "  Admin: admin@tripstars.com / Admin@123"
echo -e "  Manager: manager@tripstars.com / Manager@123"
echo -e "  Member: member@tripstars.com / Member@123"
echo -e "${BLUE}========================================${NC}"
