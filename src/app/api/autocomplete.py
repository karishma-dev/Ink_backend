"""
Autocomplete API Endpoint

Provides real-time text completion suggestions for the writing editor.
Supports streaming for faster perceived response time.
"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from neo4j import Session as Neo4jSession
from app.schemas.autocomplete import AutocompleteRequest, AutocompleteResponse
from app.services.autocomplete_service import AutocompleteService
from app.db.database import get_db
from app.db.repositories.persona_repository import PersonaRepository
from app.core.security import get_current_user
from app.core.neo4j_dependency import get_neo4j_db
from app.core.rate_limiter import limiter, RATE_LIMITS
from app.core.exceptions import ValidationException

autocomplete_router = APIRouter()

@autocomplete_router.post("/")
@limiter.limit("60/minute")  # Higher limit for autocomplete (fast, lightweight)
async def get_autocomplete(
    autocomplete_data: AutocompleteRequest,
    request: Request,
    neo4j_db: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """
    Get autocomplete suggestion for the given context.
    
    Streams the suggestion token by token for faster perceived response.
    """
    # Validate context length
    if len(autocomplete_data.context) < 10:
        raise ValidationException(
            message="Context too short. Provide at least 10 characters.",
            code="AUTOCOMPLETE_001"
        )
    
    if len(autocomplete_data.context) > 5000:
        raise ValidationException(
            message="Context too long. Maximum 5000 characters.",
            code="AUTOCOMPLETE_002"
        )
    
    # Get persona if provided
    persona = None
    if autocomplete_data.persona_id:
        persona_repo = PersonaRepository(neo4j_db)
        persona = persona_repo.get_persona(autocomplete_data.persona_id)
    
    autocomplete_service = AutocompleteService()
    
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating...'})}\n\n"
            
            full_suggestion = ""
            for chunk in autocomplete_service.get_suggestion_stream(
                context=autocomplete_data.context,
                persona=persona,
                max_tokens=autocomplete_data.max_tokens
            ):
                full_suggestion += chunk
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done', 'suggestion': full_suggestion})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@autocomplete_router.post("/sync", response_model=AutocompleteResponse)
@limiter.limit("60/minute")
async def get_autocomplete_sync(
    autocomplete_data: AutocompleteRequest,
    request: Request,
    neo4j_db: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    """
    Get autocomplete suggestion (non-streaming version).
    
    Use this if streaming is not needed or for simpler integration.
    """
    # Validate context length
    if len(autocomplete_data.context) < 10:
        raise ValidationException(
            message="Context too short. Provide at least 10 characters.",
            code="AUTOCOMPLETE_001"
        )
    
    if len(autocomplete_data.context) > 5000:
        raise ValidationException(
            message="Context too long. Maximum 5000 characters.",
            code="AUTOCOMPLETE_002"
        )
    
    # Get persona if provided
    persona = None
    if autocomplete_data.persona_id:
        persona_repo = PersonaRepository(neo4j_db)
        persona = persona_repo.get_persona(autocomplete_data.persona_id)
    
    autocomplete_service = AutocompleteService()
    
    try:
        suggestion = autocomplete_service.get_suggestion(
            context=autocomplete_data.context,
            persona=persona,
            max_tokens=autocomplete_data.max_tokens
        )
        return AutocompleteResponse(suggestion=suggestion, status="success")
    except Exception as e:
        return AutocompleteResponse(suggestion="", status="error")
