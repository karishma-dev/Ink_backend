from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class TextSelection(BaseModel):
    """Represents selected text in the editor"""
    start: int  # Character position
    end: int    # Character position
    text: str   # The selected text

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None
    persona_id: Optional[str] = None
    test_mode: Optional[bool] = False
    document_ids: Optional[list[int]] = None  # For RAG context (also used for @ mentions)
    
    # Editor context - if present, AI can edit the document
    draft_id: Optional[int] = None
    draft_content: Optional[str] = None  # If present, AI decides to edit or answer
    selection: Optional[TextSelection] = None  # User's text selection (if any)

class Citation(BaseModel):
    index: int
    document_id: int
    chunk_text: str
    score: float

class EditAction(BaseModel):
    """Represents a single edit operation on the document"""
    type: Literal["replace", "insert", "delete"]
    start: int  # Character position
    end: int    # Character position
    original: str  # Original text (for diff display)
    replacement: str  # New text (empty for delete)

class ChatResponse(BaseModel):
    response: str
    status: str
    chat_id: Optional[int] = None
    system_prompt: Optional[str] = None
    citations: Optional[list[Citation]] = None
    
    # Edit mode response
    edits: Optional[list[EditAction]] = None  # Structured edits for frontend to apply

class ChatListItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    last_message: str

class ChatListResponse(BaseModel):
    chats: List[ChatListItem]

class MessageResponse(BaseModel):
    id: int
    content: str
    role: str
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    chat_id: int
    title: str
    created_at: datetime
    messages: List[MessageResponse]