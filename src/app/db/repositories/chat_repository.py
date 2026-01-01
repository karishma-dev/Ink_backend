from typing import Optional
from app.db.models import Chat, Message

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