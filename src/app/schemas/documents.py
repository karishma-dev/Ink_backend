from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentResponse(BaseModel):
    """Single document response"""
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    """List of documents with pagination"""
    documents: List[DocumentResponse]
    total: int

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: Optional[datetime]