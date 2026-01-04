from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import chat, auth, personas, documents, drafts, autocomplete
from app.api.collaboration import collab_router
from dotenv import load_dotenv
from app.db.database import init_db
from app.core.error_handler import (
    app_exception_handler, 
    validation_exception_handler, 
    generic_exception_handler
)
from app.core.exceptions import AppException
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler

load_dotenv()

app = FastAPI(
    title="AI Writing Assistant API",
    description="Backend API for AI-powered writing assistant with RAG capabilities",
    version="1.0.0"
)

# Add rate limiter state to app
app.state.limiter = limiter

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers (order matters: specific first, generic last)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(chat.chat_router, prefix="/api", tags=["Chat"])
app.include_router(auth.auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(personas.personas_router, prefix="/api", tags=["Personas"])
app.include_router(documents.documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(drafts.drafts_router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(autocomplete.autocomplete_router, prefix="/api/autocomplete", tags=["Autocomplete"])
app.include_router(collab_router, prefix="/api/collab", tags=["Collaboration"])

# Initialize database
init_db()