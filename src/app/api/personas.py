from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from neo4j import Session as Neo4jSession
from app.core.security import get_current_user
from app.core.neo4j_dependency import get_neo4j_db
from app.db.repositories.persona_repository import PersonaRepository
from app.schemas.persona import CreatePersonaRequest, PersonaListResponse, PersonaResponse, UpdatePersonaRequest
from typing import List

personas_router = APIRouter()

@personas_router.post("/personas", response_model=PersonaResponse)
async def create_persona(
    request: CreatePersonaRequest,
    neo4j_session: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """Create a new persona for the authenticated user"""
    repo = PersonaRepository(neo4j_session)

    persona_data = {
        "name": request.name,
        "description": request.description,
        "samples": request.samples,
        "formality_level": request.formality_level,
        "creativity_level": request.creativity_level,
        "sentence_length": request.sentence_length,
        "use_metaphors": request.use_metaphors,
        "jargon_level": request.jargon_level,
        "banned_words": request.banned_words,
        "topics": request.topics,
        "audience": request.audience,
        "purpose": request.purpose
    }

    result = repo.create_persona(user_id, persona_data)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create persona")
    
    return result

@personas_router.get("/personas", response_model=PersonaListResponse)
async def list_personas(
    neo4j_session: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """Get all personas for the authenticated user"""
    repo = PersonaRepository(neo4j_session)
    personas = repo.get_user_personas(user_id)

    return PersonaListResponse(personas=personas)

@personas_router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona_by_id(
    persona_id: str,
    neo4j_session: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """Get a specific persona by ID"""
    repo = PersonaRepository(neo4j_session)
    persona = repo.get_persona(persona_id)

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return persona

@personas_router.put("/personas/{persona_id}", response_model=PersonaResponse)
async def edit_persona(
    persona_id: str,
    request: UpdatePersonaRequest,
    neo4j_session: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """Update a persona"""
    repo = PersonaRepository(neo4j_session)

    # Filter out None values (only update provided fields)
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = repo.update_persona(persona_id, updates)

    if not result:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return result

@personas_router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    neo4j_session: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """Delete a persona"""
    repo = PersonaRepository(neo4j_session)

    # Check if persona exists first
    persona = repo.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    repo.delete_persona(persona_id)

    return {"message": "Persona deleted successfully", "persona_id": persona_id}