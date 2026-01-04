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
            # Generate a title from the first 50 chars of the user message
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            chat = Chat(user_id=user_id, title=title)
            self.db.add(chat)
            self.db.flush() # Get chat.id before committing

        user_msg = Message(content=user_message, role='user', chat_id=chat.id)
        self.db.add(user_msg)
        self.db.flush() # Ensure user message has an earlier ID/timestamp

        ai_msg = Message(content=ai_response, role='assistant', chat_id=chat.id)
        self.db.add(ai_msg)
        
        self.db.commit()

        return chat.id
    
    def get_chat_history(self, user_id: int, limit: int = 20, offset: int = 0):
        """Get all chats for a user with the real last message"""
        # Subquery to get the latest message ID for each chat
        latest_msg_id_subquery = (
            select(func.max(Message.id))
            .group_by(Message.chat_id)
            .scalar_subquery()
        )

        query = (
            select(
                Chat.id,
                Chat.title,
                Chat.created_at,
                Chat.updated_at if hasattr(Chat, 'updated_at') else Chat.created_at,
                Message.content.label('last_message')
            )
            .join(Message, Chat.id == Message.chat_id)
            .filter(
                Chat.user_id == user_id,
                Message.id.in_(latest_msg_id_subquery)
            )
            .order_by(Chat.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        chats = self.db.execute(query).all()

        return {
            "chats": [
                {
                    "id": row.id,
                    "title": row.title,
                    "created_at": row.created_at,
                    "last_message": row.last_message
                } for row in chats
            ],
            "total": self.db.query(Chat).filter(Chat.user_id == user_id).count()
        }

    def get_chat_messages(self, user_id: int, chat_id: int, limit: int = 20, offset: int = 0):
        """Get full chat with all messages, ensuring user owns it"""
        chat_query = self.db.query(Chat).filter(Chat.user_id == user_id, Chat.id == chat_id).first()
        if not chat_query:
            return None
        
        query = self.db.query(Message).filter(Message.chat_id == chat_id)
        messages = query.order_by(Message.id.asc()).offset(offset).limit(limit).all() 

        return {
            "messages": messages,
            "chat_id": chat_query.id,
            "title": chat_query.title,
            "created_at": chat_query.created_at,
            "total": query.count()
        }
    
    def delete_chat_by_id(self, id: int):
        chat = self.db.query(Chat).filter(Chat.id == id).first()
        if chat:
            self.db.delete(chat)
            self.db.commit()
            return True
        return False