from fastapi import APIRouter, Depends, HTTPException, Request
from app.db.database import get_db
from app.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.services.auth_service import AuthService
from app.core.neo4j_dependency import get_neo4j_db
from app.core.exceptions import AuthException, ValidationException
from app.core.error_codes import AUTH_001, AUTH_002
from app.core.logger import logger
from app.core.rate_limiter import limiter, RATE_LIMITS

auth_router = APIRouter()

@auth_router.post("/register", response_model=AuthResponse)
@limiter.limit(RATE_LIMITS["auth"])
def register(request: Request, register_data: RegisterRequest, db: Session = Depends(get_db), neo4j_db = Depends(get_neo4j_db)):
    try:
        user_repo = UserRepository(db, neo4j_db)

        # Check for duplicate email
        existing_user = user_repo.get_user_by_email(register_data.email)
        if existing_user:
            raise AuthException(
                message="Email already registered",
                code=AUTH_002,
                status_code=400
            )
        
        # Check for duplicate username
        existing_username = user_repo.get_user_by_username(register_data.username)
        if existing_username:
            raise AuthException(
                message="Username already taken",
                code="USERNAME_EXISTS",
                status_code=400
            )
        
        new_user = user_repo.create_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password
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
@limiter.limit(RATE_LIMITS["auth"])
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user_repo = UserRepository(db, None)
        user = user_repo.get_user_by_email(login_data.email)

        if not user or not AuthService.verify_password(login_data.password, user.password):
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