from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.models.user import UserInDB
from app.core.security import get_password_hash
from app.db.mongodb import get_database
from app.api.deps import get_current_user, require_role
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(require_role(["admin"]))
):
    """
    Create a new user (Admin only)
    - Validates unique email
    - Hashes password
    - Stores in MongoDB
    """
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate role
    valid_roles = ["admin", "manager", "team_member"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Create user document
    user_in_db = UserInDB(
        id=str(uuid.uuid4()),
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    # Convert to dict and serialize datetime
    user_dict = user_in_db.model_dump()
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    user_dict["updated_at"] = user_dict["updated_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Return response without password
    return UserResponse(
        id=user_in_db.id,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at
    )

@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    List all users (Admin and Manager only)
    """
    db = get_database()
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    
    # Convert datetime strings
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        elif 'created_at' not in user:
            user['created_at'] = datetime.now(timezone.utc)
        
        if isinstance(user.get('updated_at'), str):
            user['updated_at'] = datetime.fromisoformat(user['updated_at'])
        elif 'updated_at' not in user:
            user['updated_at'] = datetime.now(timezone.utc)
    
    return [UserResponse(**user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(require_role(["admin", "manager"]))
):
    """
    Get user by ID (Admin and Manager only)
    """
    db = get_database()
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert datetime strings
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    elif 'created_at' not in user:
        user['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(user.get('updated_at'), str):
        user['updated_at'] = datetime.fromisoformat(user['updated_at'])
    elif 'updated_at' not in user:
        user['updated_at'] = datetime.now(timezone.utc)
    
    return UserResponse(**user)
