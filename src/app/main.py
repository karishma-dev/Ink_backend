from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, auth, personas
from dotenv import load_dotenv
from app.db.database import init_db

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.chat_router, prefix="/api")
app.include_router(auth.auth_router, prefix="/api/auth")
app.include_router(personas.personas_router, prefix="/api")
init_db()