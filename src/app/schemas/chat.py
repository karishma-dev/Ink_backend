from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    status: str
    chat_id: Optional[int] = None