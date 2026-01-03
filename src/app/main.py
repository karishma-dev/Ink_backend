from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, auth, personas, documents
from dotenv import load_dotenv
from app.db.database import init_db
from fastapi.exceptions import RequestValidationError
from app.core.error_handler import exception_handler
from app.core.exceptions import AppException

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, exception_handler)

app.include_router(chat.chat_router, prefix="/api")
app.include_router(auth.auth_router, prefix="/api/auth")
app.include_router(personas.personas_router, prefix="/api")
app.include_router(documents.documents_router, prefix="/api/documents")
init_db()