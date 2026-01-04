from app.db.models import Draft
from datetime import datetime

class DraftRepository:
    def __init__(self, db_session):
        self.db = db_session

    def create_draft(self, user_id: int, title: str, content: str = "") -> Draft:
        """Create a new draft"""
        draft = Draft(
            user_id=user_id,
            title=title,
            content=content,
            status="draft"
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft
    
    def get_draft_by_id(self, draft_id: int) -> Draft | None:
        """Get a draft by ID"""
        return self.db.query(Draft).filter(Draft.id == draft_id).first()
    
    def list_user_drafts(self, user_id: int, limit: int = 20, offset: int = 0) -> dict:
        """List all drafts for a user with pagination"""
        query = self.db.query(Draft).filter(Draft.user_id == user_id)
        total = query.count()
        drafts = query.order_by(Draft.updated_at.desc()).offset(offset).limit(limit).all()
        return {
            "drafts": drafts,
            "total": total
        }
    
    def update_draft(self, draft_id: int, title: str = None, content: str = None, status: str = None) -> Draft | None:
        """Update a draft"""
        draft = self.get_draft_by_id(draft_id)
        if not draft:
            return None
        
        if title is not None:
            draft.title = title
        if content is not None:
            draft.content = content
        if status is not None:
            draft.status = status
        
        # Explicitly update the timestamp
        draft.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(draft)
        return draft
    
    def delete_draft(self, draft_id: int) -> bool:
        """Delete a draft"""
        draft = self.get_draft_by_id(draft_id)
        if not draft:
            return False
        
        self.db.delete(draft)
        self.db.commit()
        return True
