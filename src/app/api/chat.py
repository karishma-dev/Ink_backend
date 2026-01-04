import json
from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatListResponse
from app.services.gemini_service import GeminiService
from app.services.prompt_builder import PromptBuilder
from google.genai.errors import ClientError
from app.db.database import get_db
from app.db.repositories.chat_repository import ChatRepository
from app.db.repositories.persona_repository import PersonaRepository
from app.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.core.neo4j_dependency import get_neo4j_db
from neo4j import Session as Neo4jSession
from app.services.tools_service import ToolsService
from app.services.rag_service import RAGService
from app.services.edit_service import EditService
from fastapi.responses import StreamingResponse
from app.core.rate_limiter import limiter, RATE_LIMITS

chat_router = APIRouter()

@chat_router.post("/chat")
@limiter.limit(RATE_LIMITS["chat"])
async def chat_endpoint(
    chat_data: ChatRequest,
    request: Request,  # Required for rate limiting
    db: Session = Depends(get_db),
    neo4j_db: Neo4jSession = Depends(get_neo4j_db),
    user_id: int = Depends(get_current_user)
):
    def generate():
        try:
            # Get persona (use explicitly provided or fall back to active persona)
            neo4j_repo = PersonaRepository(neo4j_db)
            user_repo = UserRepository(db, None)
            persona = None

            # Priority: 1. Explicit persona_id, 2. User's active persona
            persona_id_to_use = chat_data.persona_id
            if not persona_id_to_use:
                persona_id_to_use = user_repo.get_active_persona_id(user_id)
            
            if persona_id_to_use:
                persona = neo4j_repo.get_persona(persona_id_to_use)
            
            # Initialize shared variables for saving
            full_response = ""
            citations = []
            active_chat_id = None

            # If draft_content is present, user is in editor - AI decides to edit or answer
            if chat_data.draft_content:
                yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing...'})}\n\n"
                
                edit_service = EditService()
                selection_dict = None
                if chat_data.selection:
                    selection_dict = {
                        "start": chat_data.selection.start,
                        "end": chat_data.selection.end,
                        "text": chat_data.selection.text
                    }
                
                result = edit_service.generate_edits(
                    document_content=chat_data.draft_content,
                    instruction=chat_data.message,
                    selection=selection_dict,
                    persona=persona
                )
                
                response_type = result.get("response_type", "edit")
                explanation = result.get("explanation", "")
                
                # Stream the explanation/answer
                if explanation:
                    yield f"data: {json.dumps({'type': 'content', 'content': explanation})}\n\n"
                
                full_response = explanation
                
                # Only send edits if AI decided to make changes
                if response_type == "edit":
                    edits = result.get("edits", [])
                    yield f"data: {json.dumps({'type': 'edits', 'edits': edits})}\n\n"
            
            # Regular chat mode (no document context)
            else:
                yield f"data: {json.dumps({'type': 'status', 'content': 'Thinking...'})}\n\n"
                
                # Get RAG document context (also handles @ mentions via document_ids)
                document_context = ""
                citations = []
                
                if chat_data.document_ids:
                    yield f"data: {json.dumps({'type': 'status', 'content': 'Searching documents...'})}\n\n"

                    rag_service = RAGService()
                    rag_result = rag_service.get_relevant_context(
                        query=chat_data.message,
                        document_ids=chat_data.document_ids
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
                
                for event in gemini_service.chat(chat_data.message, system_prompt):
                    if event["type"] == "content":
                        full_response += event["content"]
                    yield f"data: {json.dumps(event)}\n\n"
            
            # Save to DB (for both edit and ask modes)
            repo = ChatRepository(db)
            chat_id = repo.save_message(
                user_id=user_id,
                chat_id=chat_data.chat_id or active_chat_id,
                user_message=chat_data.message,
                ai_response=full_response
            )
            
            yield f"data: {json.dumps({'type': 'done', 'chat_id': chat_id, 'citations': citations, 'mode': 'edit' if chat_data.draft_content else 'ask'})}\n\n"

        except Exception as e:
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
        return chats
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
        messages = repo.get_chat_messages(user_id, chat_id, limit, offset)
        return messages
    except ClientError as e:
        raise HTTPException(status_code=500, detail="Error fetching chats")