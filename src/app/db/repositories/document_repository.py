from app.db.models import Documents

class DocumentRepository:
    def __init__(self, db_session):
        self.db = db_session

    def create_document(self, user_id: int, filename: str, file_type: str, file_size: int):
        document = Documents(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            status="processing"
        )
        self.db.add(document)
        self.db.commit()
        return document
    
    def update_document_status(self, document_id: int, status: str):
        document = self.db.query(Documents).filter(Documents.id == document_id).first()
        if document:
            document.status = status
            self.db.commit()
        return document

    def get_document_by_id(self, id: int):
        return self.db.query(Documents).filter(Documents.id == id).first()

    def list_user_documents(self, user_id: int, limit: int = 20, offset: int = 0):
        query = self.db.query(Documents).filter(Documents.user_id == user_id)
        documents = query.order_by(Documents.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "documents": documents,
            "total": query.count()
        }

    def delete_document(self, id: int):
        document = self.db.query(Documents).filter(Documents.id == id).first()
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
