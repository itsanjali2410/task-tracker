from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.db.mongodb import get_database
from app.schemas.user import UserResponse
from app.api.deps import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Login endpoint
    - Validates email and password
    - Returns JWT token and user data
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
        user=user_response.model_dump()
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user
