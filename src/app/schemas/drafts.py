from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DraftCreate(BaseModel):
    """Request body for creating a draft"""
    title: str
    content: Optional[str] = ""

class DraftUpdate(BaseModel):
    """Request body for updating a draft"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class DraftResponse(BaseModel):
    """Single draft response"""
    id: int
    title: str
    content: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DraftListResponse(BaseModel):
    """List of drafts with pagination"""
    drafts: list[DraftResponse]
    total: int
