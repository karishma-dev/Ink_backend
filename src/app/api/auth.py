from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.services.auth_service import AuthService
from app.core.neo4j_dependency import get_neo4j_db

auth_router = APIRouter()

@auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db), neo4j_db = Depends(get_neo4j_db)):
    user_repo = UserRepository(db, neo4j_db)
    existing_user = user_repo.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = user_repo.create_user(
        username=request.username,
        email=request.email,
        password=request.password
    )
    token = AuthService.create_access_token(new_user.id)
    return AuthResponse(user_id=new_user.id, access_token=token)

@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db, None)
    user = user_repo.get_user_by_email(request.email)
    if not user or not AuthService.verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = AuthService.create_access_token(user.id)
    return AuthResponse(user_id=user.id, access_token=token)