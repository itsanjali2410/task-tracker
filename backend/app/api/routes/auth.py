from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.db.mongodb import get_database
from app.schemas.user import UserResponse
from app.api.deps import get_current_user
from app.models.refresh_token import RefreshTokenInDB
from datetime import datetime, timezone, timedelta
from app.core.config import settings
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Login endpoint
    - Validates email and password
    - Returns access token, refresh token, and user data
    """
    db = get_database()
    user = await db.users.find_one({"email": login_data.email})
    
    # Handle both old 'password' field and new 'hashed_password' field
    password_field = user.get("hashed_password") or user.get("password") if user else None
    
    if not user or not password_field or not verify_password(login_data.password, password_field):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    
    # Create refresh token
    refresh_token = create_refresh_token()
    
    # Store refresh token in database
    refresh_token_doc = RefreshTokenInDB(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    refresh_dict = refresh_token_doc.model_dump()
    refresh_dict["created_at"] = refresh_dict["created_at"].isoformat()
    refresh_dict["expires_at"] = refresh_dict["expires_at"].isoformat()
    
    await db.refresh_tokens.insert_one(refresh_dict)
    
    # Remove sensitive fields
    user.pop("_id", None)
    user.pop("hashed_password", None)
    user.pop("password", None)
    
    # Convert datetime strings and add defaults if missing
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    elif 'created_at' not in user:
        user['created_at'] = datetime.now(timezone.utc)
    
    if isinstance(user.get('updated_at'), str):
        user['updated_at'] = datetime.fromisoformat(user['updated_at'])
    elif 'updated_at' not in user:
        user['updated_at'] = datetime.now(timezone.utc)
    
    # Ensure is_active exists
    if 'is_active' not in user:
        user['is_active'] = True
    
    user_response = UserResponse(**user)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user=user_response.model_dump()
    )

@router.post("/refresh")
async def refresh_access_token(refresh_token: str):
    """
    Refresh token endpoint
    - Validates refresh token
    - Issues new access token
    """
    db = get_database()
    
    # Find refresh token
    token_doc = await db.refresh_tokens.find_one({"token": refresh_token}, {"_id": 0})
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if revoked
    if token_doc.get("is_revoked"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Check if expired
    expires_at = token_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user
    user = await db.users.find_one({"id": token_doc["user_id"]}, {"_id": 0})
    
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(refresh_token: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Logout endpoint
    - Revokes refresh token
    """
    db = get_database()
    
    await db.refresh_tokens.update_one(
        {"token": refresh_token, "user_id": current_user.id},
        {"$set": {"is_revoked": True}}
    )
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user
