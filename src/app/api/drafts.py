from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFound, ValidationException
from app.db.repositories.draft_repository import DraftRepository
from app.schemas.drafts import DraftCreate, DraftUpdate, DraftResponse, DraftListResponse

drafts_router = APIRouter()

@drafts_router.post("/", response_model=DraftResponse)
async def create_draft(
    draft_data: DraftCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Create a new draft"""
    repo = DraftRepository(db)
    draft = repo.create_draft(
        user_id=user_id,
        title=draft_data.title,
        content=draft_data.content or ""
    )
    return DraftResponse.model_validate(draft)

@drafts_router.get("/", response_model=DraftListResponse)
async def list_drafts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all drafts for current user"""
    repo = DraftRepository(db)
    result = repo.list_user_drafts(user_id, limit, offset)
    return {
        "drafts": [DraftResponse.model_validate(d) for d in result["drafts"]],
        "total": result["total"]
    }

@drafts_router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get a specific draft (user must own it)"""
    repo = DraftRepository(db)
    draft = repo.get_draft_by_id(draft_id)
    
    if not draft:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    if draft.user_id != user_id:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    return DraftResponse.model_validate(draft)

@drafts_router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: int,
    draft_data: DraftUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Update a draft (user must own it)"""
    repo = DraftRepository(db)
    draft = repo.get_draft_by_id(draft_id)
    
    if not draft:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    if draft.user_id != user_id:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    # Validate status if provided
    if draft_data.status and draft_data.status not in ["draft", "published", "archived"]:
        raise ValidationException(
            message="Invalid status. Must be 'draft', 'published', or 'archived'",
            code="DRAFT_002"
        )
    
    updated_draft = repo.update_draft(
        draft_id=draft_id,
        title=draft_data.title,
        content=draft_data.content,
        status=draft_data.status
    )
    
    return DraftResponse.model_validate(updated_draft)

@drafts_router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Delete a draft (user must own it)"""
    repo = DraftRepository(db)
    draft = repo.get_draft_by_id(draft_id)
    
    if not draft:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    if draft.user_id != user_id:
        raise NotFound(message="Draft not found", code="DRAFT_001")
    
    repo.delete_draft(draft_id)
    
    return {"message": "Draft deleted successfully"}
