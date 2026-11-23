"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ...schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from ...services.auth_service import create_user, authenticate_user, create_access_token
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, user_data.email, user_data.password, user_data.full_name)
        token = create_access_token({"sub": user.id})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
