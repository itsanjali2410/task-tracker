from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.api.routes import auth, users, tasks, comments
from app.api.deps import get_current_user
from app.core.security import get_password_hash
import logging
import uuid
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database events
@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB and seed initial data"""
    await connect_to_mongo()
    await seed_initial_data()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection"""
    await close_mongo_connection()

# Seed initial users
async def seed_initial_data():
    """Create initial seed users if they don't exist"""
    db = get_database()
    
    # Check if admin exists
    existing_admin = await db.users.find_one({"email": "admin@tripstars.com"})
    
    if not existing_admin:
        logger.info("Seeding initial users...")
        
        seed_users = [
            {
                "id": str(uuid.uuid4()),
                "email": "admin@tripstars.com",
                "full_name": "Admin User",
                "hashed_password": get_password_hash("Admin@123"),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "manager@tripstars.com",
                "full_name": "Manager User",
                "hashed_password": get_password_hash("Manager@123"),
                "role": "manager",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "member@tripstars.com",
                "full_name": "Team Member",
                "hashed_password": get_password_hash("Member@123"),
                "role": "team_member",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        await db.users.insert_many(seed_users)
        logger.info("Seed users created successfully")
    else:
        logger.info("Seed users already exist")

# Include routers with /api prefix
api_prefix = "/api"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(tasks.router, prefix=api_prefix)
app.include_router(comments.router, prefix=api_prefix)

# Health check and stats endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/api/stats")
async def get_stats(current_user = Depends(get_current_user)):
    """
    Get task statistics
    - Team members see their own stats
    - Admins and Managers see all stats
    """
    db = get_database()
    
    if current_user.role == "team_member":
        tasks = await db.tasks.find({"assigned_to": current_user.id}, {"_id": 0}).to_list(1000)
    else:
        tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    
    total_tasks = len(tasks)
    todo = len([t for t in tasks if t["status"] == "todo"])
    in_progress = len([t for t in tasks if t["status"] == "in_progress"])
    completed = len([t for t in tasks if t["status"] == "completed"])
    
    return {
        "total_tasks": total_tasks,
        "todo": todo,
        "in_progress": in_progress,
        "completed": completed
    }

from app.api.deps import get_current_user
from fastapi import Depends

@app.get("/api")
async def root():
    """Root API endpoint"""
    return {
        "message": "TripStars Task Management API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }
