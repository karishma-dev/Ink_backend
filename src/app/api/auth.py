from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.services.auth_service import AuthService
from app.core.neo4j_dependency import get_neo4j_db
from app.core.exceptions import AuthException, ValidationException
from app.core.error_codes import AUTH_001, AUTH_002
from app.core.logger import logger

auth_router = APIRouter()

@auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db), neo4j_db = Depends(get_neo4j_db)):
    try:
        user_repo = UserRepository(db, neo4j_db)

        existing_user = user_repo.get_user_by_email(request.email)
        if existing_user:
            raise AuthException(
                message="Email already registered",
                code=AUTH_002,
                status_code=400
            )
        
        new_user = user_repo.create_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        token = AuthService.create_access_token(new_user.id)
        logger.info(f"User registered: {new_user.email}")
        return AuthResponse(user_id=new_user.id, access_token=token)
    
    except AuthException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise AuthException(
            message="Registration failed",
            code="REGISTRATION_ERROR",
            status_code=500
        )

@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user_repo = UserRepository(db, None)
        user = user_repo.get_user_by_email(request.email)

        if not user or not AuthService.verify_password(request.password, user.password):
            raise AuthException(
                message="Invalid credentials",
                code=AUTH_001,
                status_code=401
            )
        
        token = AuthService.create_access_token(user.id)
        return AuthResponse(user_id=user.id, access_token=token)
    except AuthException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise AuthException(
            message="Login failed",
            code="LOGIN_ERROR",
            status_code=500
        )