from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None
    persona_id: Optional[str] = None
    test_mode: Optional[bool] = False
    document_ids: Optional[list[int]] = None

class Citation(BaseModel):
    index: int
    document_id: int
    chunk_text: str
    score: float
    
class ChatResponse(BaseModel):
    response: str
    status: str
    chat_id: Optional[int] = None
    system_prompt: Optional[str] = None
    citations: Optional[list[Citation]] = None

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