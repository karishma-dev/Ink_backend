from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiService
from google.genai.errors import ClientError
from app.db.database import get_db
from app.db.repositories.chat_repository import ChatRepository
from sqlalchemy.orm import Session
from app.core.security import get_current_user

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    gemini_service = GeminiService()
    try:
        response_text = gemini_service.chat(request.message)

        repo = ChatRepository(db)
        chat_id = repo.save_message(
            user_id=user_id,
            chat_id=request.chat_id,
            user_message=request.message,
            ai_response=response_text
        )
        return ChatResponse(response=response_text, status="success", chat_id=chat_id)
    except ClientError as e:
        return ChatResponse(response=str(e), status="error")