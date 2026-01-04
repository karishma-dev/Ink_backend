from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Optional

users_router = APIRouter()

class SetActivePersonaRequest(BaseModel):
    persona_id: str

class ActivePersonaResponse(BaseModel):
    persona_id: Optional[str]

@users_router.put("/active-persona", response_model=ActivePersonaResponse)
def set_active_persona(
    request: SetActivePersonaRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Set the active persona for the current user"""
    user_repo = UserRepository(db, None)
    user_repo.set_active_persona(user_id, request.persona_id)
    return ActivePersonaResponse(persona_id=request.persona_id)

@users_router.delete("/active-persona", response_model=ActivePersonaResponse)
def clear_active_persona(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Clear the active persona for the current user"""
    user_repo = UserRepository(db, None)
    user_repo.clear_active_persona(user_id)
    return ActivePersonaResponse(persona_id=None)

@users_router.get("/active-persona", response_model=ActivePersonaResponse)
def get_active_persona(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get the active persona for the current user"""
    user_repo = UserRepository(db, None)
    persona_id = user_repo.get_active_persona_id(user_id)
    return ActivePersonaResponse(persona_id=persona_id)
