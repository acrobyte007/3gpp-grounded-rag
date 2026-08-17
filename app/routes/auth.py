from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.database.database import db_manager
from app.database.repositories import UserRepository
from app.services.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    async with db_manager.connect() as session:
        repo = UserRepository(session)
        
        existing_user = await repo.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await repo.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user = await repo.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=user.created_at
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    async with db_manager.connect() as session:
        repo = UserRepository(session)
        
        user = await repo.authenticate_user(
            username=user_data.username,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )