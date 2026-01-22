from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.user import UserCreate, UserResponse, UserUpdate, PasswordReset
from app.models.user import UserInDB
from app.core.security import get_password_hash
from app.db.mongodb import get_database
from app.api.deps import get_current_user, require_role
from app.services.audit_service import log_audit
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
    
    # Log audit
    await log_audit(
        action_type="user_created",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        metadata={
            "new_user_email": user_data.email,
            "new_user_role": user_data.role
        }
    )
    
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

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserResponse = Depends(require_role(["admin"]))
):
    """
    Update user details (Admin only)
    - Can update email, full_name, role, is_active
    - Cannot update password (use password reset endpoint)
    """
    db = get_database()
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Check email uniqueness if updating email
    if "email" in update_data and update_data["email"] != user["email"]:
        existing = await db.users.find_one({"email": update_data["email"]})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Validate role if updating
    if "role" in update_data:
        valid_roles = ["admin", "manager", "team_member"]
        if update_data["role"] not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log audit
    await log_audit(
        action_type="user_updated",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        metadata={
            "updated_user_id": user_id,
            "updated_user_email": user.get("email"),
            "changes": update_data
        }
    )
    
    # Fetch updated user
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    
    if isinstance(updated_user.get('created_at'), str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    elif 'created_at' not in updated_user:
        updated_user['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(updated_user.get('updated_at'), str):
        updated_user['updated_at'] = datetime.fromisoformat(updated_user['updated_at'])
    elif 'updated_at' not in updated_user:
        updated_user['updated_at'] = datetime.now(timezone.utc)
    
    return UserResponse(**updated_user)

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    password_data: PasswordReset,
    current_user: UserResponse = Depends(require_role(["admin"]))
):
    """
    Reset user password (Admin only)
    - Hashes new password
    - Updates user document
    """
    db = get_database()
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password
    hashed_password = get_password_hash(password_data.new_password)
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "hashed_password": hashed_password,
            "password": hashed_password,  # Update both fields for compatibility
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Revoke all refresh tokens for this user
    await db.refresh_tokens.update_many(
        {"user_id": user_id, "is_revoked": False},
        {"$set": {"is_revoked": True}}
    )
    
    # Log audit
    await log_audit(
        action_type="password_reset",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        metadata={
            "target_user_id": user_id,
            "target_user_email": user.get("email")
        }
    )
    
    return {"message": "Password reset successfully"}

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: UserResponse = Depends(require_role(["admin"]))
):
    """
    Deactivate user (Admin only)
    - Sets is_active to False
    - User cannot log in
    - Admin cannot deactivate themselves
    """
    db = get_database()
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Revoke all refresh tokens
    await db.refresh_tokens.update_many(
        {"user_id": user_id, "is_revoked": False},
        {"$set": {"is_revoked": True}}
    )
    
    # Log audit
    await log_audit(
        action_type="user_deactivated",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        metadata={
            "target_user_id": user_id,
            "target_user_email": user.get("email")
        }
    )
    
    return {"message": "User deactivated successfully"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: UserResponse = Depends(require_role(["admin"]))
):
    """
    Activate user (Admin only)
    - Sets is_active to True
    - User can log in again
    """
    db = get_database()
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit
    await log_audit(
        action_type="user_activated",
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        metadata={
            "target_user_id": user_id,
            "target_user_email": user.get("email")
        }
    )
    
    return {"message": "User activated successfully"}
