from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, DateTime, Text, UniqueConstraint
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

class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'processing', 'completed', 'failed'
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, default=datetime.utcnow)
    chunks: Mapped[List["DocumentChunks"]] = relationship("DocumentChunks", backref="document", cascade="all, delete-orphan")

class DocumentChunks(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[Optional[str]] = mapped_column(DateTime, default=datetime.utcnow)