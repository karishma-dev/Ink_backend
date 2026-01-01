from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'user' or 'assistant'
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, default=datetime.utcnow)

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, default=datetime.utcnow)
    messages: Mapped[List[Message]] = relationship("Message", backref="chat")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, default=datetime.utcnow)
    chats: Mapped[List[Chat]] = relationship("Chat", backref="user")