from pydantic import BaseModel
from typing import Optional

class AutocompleteRequest(BaseModel):
    """Request for autocomplete suggestions"""
    context: str  # Text before cursor (last 2-3 sentences)
    persona_id: Optional[str] = None  # Optional persona for style matching
    max_tokens: int = 50  # Max tokens for suggestion

class AutocompleteResponse(BaseModel):
    """Response with autocomplete suggestion"""
    suggestion: str
    status: str  # "success" or "error"
