from typing import Optional
from app.db.models import User
from app.services.auth_service import AuthService

class UserRepository:
    def __init__(self, db_session):
        self.db = db_session

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, username: str, email: str, password: str) -> User:
        hash_password = AuthService.hash_password(password)
        new_user = User(username=username, email=email, password=hash_password)
        self.db.add(new_user)
        self.db.commit()
        return new_user