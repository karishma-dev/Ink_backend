from pydantic import BaseModel, Field
from typing import Optional, List

class CreatePersonaRequest(BaseModel):
    name: str
    description: str
    samples: List[str]
    formality_level: int
    creativity_level: int
    sentence_length: str
    use_metaphors: bool
    jargon_level: int
    banned_words: List[str] = []
    topics: List[str] = []
    audience: str = "general"
    purpose: str = "blog"

class PersonaResponse(BaseModel):
    id: str
    name: str
    description: str
    samples: List[str]
    formality_level: int
    creativity_level: int
    sentence_length: str
    use_metaphors: bool
    jargon_level: int
    banned_words: List[str]
    topics: List[str]
    audience: str
    purpose: str
    created_at: str
    updated_at: str

class UpdatePersonaRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    samples: Optional[List[str]] = None
    formality_level: Optional[int] = None
    creativity_level: Optional[int] = None
    sentence_length: Optional[str] = None
    use_metaphors: Optional[bool] = None
    jargon_level: Optional[int] = None
    banned_words: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    audience: Optional[str] = None
    purpose: Optional[str] = None

class PersonaListResponse(BaseModel):
    personas: List[PersonaResponse]