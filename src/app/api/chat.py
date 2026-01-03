import json
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatListResponse
from app.services.gemini_service import GeminiService
from app.services.prompt_builder import PromptBuilder
from google.genai.errors import ClientError
from app.db.database import get_db
from app.db.repositories.chat_repository import ChatRepository
from app.db.repositories.persona_repository import PersonaRepository
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.core.neo4j_dependency import get_neo4j_db
from neo4j import Session as Neo4jSession
from app.services.tools_service import ToolsService
from app.services.rag_service import RAGService
from fastapi.responses import StreamingResponse

chat_router = APIRouter()

@chat_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    db: Session = Depends(get_db),
    neo4j_db: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'status', 'content': 'Thinking...'})}\n\n"

            # Get persona
            neo4j_repo = PersonaRepository(neo4j_db)
            persona = None

            if request.persona_id:
                persona = neo4j_repo.get_persona(request.persona_id)
            
            # Get document context
            document_context = ""
            citations = []
            
            if request.document_ids:
                yield f"data: {json.dumps({'type': 'status', 'content': 'Searching documents...'})}\n\n"

                rag_service = RAGService()

                rag_result = rag_service.get_relevant_context(
                    query=request.message,
                    document_ids=request.document_ids
                )
                document_context = rag_result["context"]
                citations = rag_result["citations"]

            system_prompt = PromptBuilder.build_full_prompt(
                persona=persona,
                document_context=document_context
            )

            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating...'})}\n\n"

            # Stream with tools
            tools_service = ToolsService(neo4j_db)
            gemini_service = GeminiService(tools_service=tools_service)
            full_response = ""
            
            for event in gemini_service.chat(request.message, system_prompt):
                if event["type"] == "content":
                    full_response += event["content"]
                yield f"data: {json.dumps(event)}\n\n"
            
            # Save to DB
            repo = ChatRepository(db)
            chat_id = repo.save_message(
                user_id=user_id,
                chat_id=request.chat_id,
                user_message=request.message,
                ai_response=full_response
            )
            
            yield f"data: {json.dumps({'type': 'done', 'chat_id': chat_id, 'citations': citations})}\n\n"

        except ClientError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
    
@chat_router.get("/chats", response_model=ChatListResponse)
async def list_user_chats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    try:
        repo = ChatRepository(db)

        chats = repo.get_chat_history(user_id, limit, offset)

        return ChatListResponse(chats=chats)
    except ClientError as e:
        return HTTPException(status_code=500, detail="Error fetching chats")
    
@chat_router.get("/chat/{chat_id}", response_model=ChatHistoryResponse)
async def list_user_messages(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
    chat_id: int = "",
    limit: int = 20,
    offset: int = 0
):
    try:
        repo = ChatRepository(db)

        messages = repo.get_chat_messages(user_id,chat_id, limit, offset)

        return ChatHistoryResponse(chat_id=chat_id, messages=messages)
    except ClientError as e:
        raise HTTPException(status_code=500, detail="Error fetching chats")