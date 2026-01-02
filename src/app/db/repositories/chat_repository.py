from typing import Optional
from app.db.models import Chat, Message
from sqlalchemy import func, select

class ChatRepository:
    def __init__(self, db_session):
        self.db = db_session

    def save_message(self, user_id: int, chat_id: Optional[int], user_message: str, ai_response: str):
        if chat_id:
            chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        else:
            chat = Chat(user_id=user_id, title="New Chat")
            self.db.add(chat)
            self.db.commit()

        user_msg = Message(content=user_message, role='user', chat_id=chat.id)
        ai_msg = Message(content=ai_response, role='assistant', chat_id=chat.id)

        self.db.add_all([user_msg, ai_msg])
        self.db.commit()

        return chat.id
    
    def get_chat_history(self, user_id: int, limit: int = 20, offset: int = 0):
        """Get all chats for a user"""
        query = select(
            Chat.id,
            Chat.title,
            Chat.created_at,
            func.max(Message.content).label('last_message')
        ).outerjoin(
            Message, Chat.id == Message.chat_id
        ).filter(
            Chat.user_id == user_id
        ).group_by(
            Chat.id, Chat.title, Chat.created_at
        ).order_by(
            Chat.created_at.desc()
        ).limit(limit).offset(offset)

        chats = self.db.execute(query).all()

        return {
            "chats": [dict(row) for row in chats],
            "total": self.db.query(Chat).filter(Chat.user_id == user_id).count()
        }

    def get_chat_messages(self, user_id: int, chat_id: int, limit: int = 20, offset: int = 0):
        """Get full chat with all messages, ensuring user owns it"""
        chat_query = self.db.query(Chat).filter(Chat.user_id == user_id, Chat.id == chat_id).first()
        if not chat_query:
            return None
        
        query = self.db.query(Message).filter(Message.chat_id == chat_id)
        messages = query.order_by(Message.created_at.asc()).offset(offset).limit(limit).all() 

        return {
            "messages": messages,
            "chat_id": chat_query.id,
            "title": chat_query.title,
            "created_at": chat_query.created_at,
            "total": query.count()
        }