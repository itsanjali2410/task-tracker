from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tripstars-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str  # 'admin', 'manager', 'team_member'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    priority: str  # 'low', 'medium', 'high'
    status: str = "todo"  # 'todo', 'in_progress', 'completed'
    assigned_to: str  # User ID
    assigned_to_email: Optional[str] = None
    assigned_to_name: Optional[str] = None
    due_date: str
    created_by: str  # User ID
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    assigned_to: str
    due_date: str

class TaskUpdate(BaseModel):
    status: str

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if user is None:
        raise credentials_exception
    return User(**user)

# Seed initial users
async def seed_users():
    existing_admin = await db.users.find_one({"email": "admin@tripstars.com"})
    if not existing_admin:
        users_to_seed = [
            {
                "id": str(uuid.uuid4()),
                "email": "admin@tripstars.com",
                "full_name": "Admin User",
                "password": get_password_hash("Admin@123"),
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "manager@tripstars.com",
                "full_name": "Manager User",
                "password": get_password_hash("Manager@123"),
                "role": "manager",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "member@tripstars.com",
                "full_name": "Team Member",
                "password": get_password_hash("Member@123"),
                "role": "team_member",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.users.insert_many(users_to_seed)
        logging.info("Seed users created")

# Routes
@api_router.get("/")
async def root():
    return {"message": "TripStars Task Management API"}

@api_router.post("/auth/login")
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email})
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    user.pop("_id", None)
    user.pop("password", None)
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/users", response_model=User)
async def create_user(user_create: UserCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    user_dict = user_create.model_dump()
    user_dict["password"] = get_password_hash(user_dict["password"])
    user_obj = User(
        id=str(uuid.uuid4()),
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        role=user_dict["role"]
    )
    
    doc = user_obj.model_dump()
    doc["password"] = user_dict["password"]
    doc["created_at"] = doc["created_at"].isoformat()
    
    await db.users.insert_one(doc)
    return user_obj

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users"
        )
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.post("/tasks", response_model=Task)
async def create_task(task_create: TaskCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can create tasks"
        )
    
    # Get assigned user details
    assigned_user = await db.users.find_one({"id": task_create.assigned_to}, {"_id": 0})
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found"
        )
    
    task_dict = task_create.model_dump()
    task_obj = Task(
        **task_dict,
        created_by=current_user.id,
        created_by_name=current_user.full_name,
        assigned_to_email=assigned_user["email"],
        assigned_to_name=assigned_user["full_name"]
    )
    
    doc = task_obj.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    
    await db.tasks.insert_one(doc)
    return task_obj

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(current_user: User = Depends(get_current_user)):
    if current_user.role == "team_member":
        # Team members only see their own tasks
        tasks = await db.tasks.find({"assigned_to": current_user.id}, {"_id": 0}).to_list(1000)
    else:
        # Admins and managers see all tasks
        tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
    return tasks

@api_router.patch("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, current_user: User = Depends(get_current_user)):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Team members can only update their own tasks
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tasks"
        )
    
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"status": task_update.status}}
    )
    
    updated_task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if isinstance(updated_task.get('created_at'), str):
        updated_task['created_at'] = datetime.fromisoformat(updated_task['created_at'])
    return Task(**updated_task)

@api_router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
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

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await seed_users()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
