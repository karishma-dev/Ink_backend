from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from app.db.repositories.document_repository import DocumentRepository
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import ValidationException, NotFound
from app.schemas.documents import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.workers.document_tasks import process_document
from pathlib import Path
import os

documents_router = APIRouter()

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}
UPLOAD_DIR = Path("uploads")

# Create uploads directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

@documents_router.post("/upload", response_model=DocumentUploadResponse)
async def upload(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user)
):
    """Upload a document (PDF, markdown, or text file)"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            message=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            code="DOC_001"
        )
    
    # Read file and validate size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise ValidationException(
            message=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB",
            code="DOC_002"
        )
    
    # Save to disk
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Save to database
    repo = DocumentRepository(db)
    document = repo.create_document(
        user_id=user_id,
        filename=file.filename,
        file_type=file_ext,
        file_size=file_size
    )
    

    process_document.delay(document.id)
    return DocumentUploadResponse.from_orm(document)

@documents_router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all documents for current user"""
    repo = DocumentRepository(db)
    result = repo.list_user_documents(user_id, limit, offset)
    return {
        "documents": [DocumentResponse.from_orm(doc) for doc in result["documents"]],
        "total": result["total"]
    }

@documents_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get a specific document (user must own it)"""
    repo = DocumentRepository(db)
    document = repo.get_document_by_id(document_id)
    
    if not document:
        raise NotFound(message="Document not found", code="DOC_003")
    
    if document.user_id != user_id:
        raise NotFound(message="Document not found", code="DOC_003")
    
    return DocumentResponse.from_orm(document)

@documents_router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Delete a document (user must own it)"""
    repo = DocumentRepository(db)
    document = repo.get_document_by_id(document_id)
    
    if not document:
        raise NotFound(message="Document not found", code="DOC_003")
    
    if document.user_id != user_id:
        raise NotFound(message="Document not found", code="DOC_003")
    
    # Delete file from disk
    file_path = UPLOAD_DIR / document.filename
    if file_path.exists():
        os.remove(file_path)
    
    # Delete from database (cascades to chunks)
    repo.delete_document(document_id)
    
    return {"message": "Document deleted successfully"}
