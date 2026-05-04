from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.services.users import UserService
from app.database.connection import get_db
from app.schemas.users import UserCreate, UserLogin, Token, UserResponse

from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_password,
    get_password_hash
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    service = UserService(db)
    
    existing = await service.get_user_by_username(user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user = await service.create_user(user_in)  # Service handles hashing
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    service = UserService(db)
    
    # Debug: Print login attempt
    print(f"🔐 Login attempt: username='{credentials.username}'")
    
    # Find user by username
    user = await service.get_user_by_username(credentials.username)
    if not user:
        print(f"❌ User not found: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ User found: {user.username}")
    print(f"📝 Stored hash: {user.password_hash[:50]}...")
    print(f"🔑 Provided password: '{credentials.password}'")
    
    # Debug: Check if password is plain text
    if user.password_hash and not user.password_hash.startswith('$2'):
        print(f"⚠️ WARNING: Password appears to be stored in plain text: '{user.password_hash}'")
        print(f"💡 This needs to be hashed. Re-hashing now...")
        # Fix the password on the fly
        hashed = get_password_hash(user.password_hash)
        user.password_hash = hashed
        await db.commit()
        print(f"✅ Password has been re-hashed")
    
    # Verify password
    is_valid = verify_password(credentials.password, user.password_hash)
    print(f"✓ Password verification result: {is_valid}")
    
    if not is_valid:
        # Helpful debug: Show what the hash should be for the provided password
        expected_hash = get_password_hash(credentials.password)
        print(f"❌ Password mismatch!")
        print(f"   Expected hash for '{credentials.password}': {expected_hash[:50]}...")
        print(f"   Actual hash in DB: {user.password_hash[:50]}...")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        print(f"❌ Account disabled: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled"
        )
    
    # Create tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    print(f"✅ Login successful for user: {user.username}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900  # 15 minutes in seconds
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    from app.core.security import decode_token
    
    payload = decode_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    service = UserService(db)
    user = await service.get_user_by_id(int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Issue new tokens
    token_data = {"sub": str(user.id)}
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)
    
    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=900
    )