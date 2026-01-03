from app.core.celery_app import app
from app.db.database import SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.services.document_processor import DocumentProcessor
from pathlib import Path
from app.db.models import DocumentChunks
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

UPLOAD_DIR = Path("uploads")

@app.task
def process_document(document_id: int):
    """Background task to process uploaded document"""

    # Create a new DB session (we're outside FastAPI request)
    db = SessionLocal()

    try:
        # 1. Get document from DB
        repo = DocumentRepository(db)
        document = repo.get_document_by_id(document_id)

        if not document:
            print(f"Document {document_id} not found")
            return

        # 2. Extract text from file
        processor = DocumentProcessor()
        file_path = UPLOAD_DIR / document.filename
        text = processor.extract_text(str(file_path), document.file_type)

        # 3. Chunk the text
        chunks = processor.chunk_text(text)

        # 4. Save chunks to database
        for index, chunk_text in enumerate(chunks):
            chunk = DocumentChunks(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=index
            )
            db.add(chunk)

        db.commit()
        db.refresh(document)

        # 5. Generate embeddings and store in Qdrant
        embedding_service = EmbeddingService()
        qdrant_service = QdrantService()

        for chunk_obj in document.chunks:
            embedding = embedding_service.generate_embedding(chunk_obj.chunk_text)
            qdrant_service.store_embedding(
                chunk_id=chunk_obj.id,
                user_id=document.user_id,
                document_id=document_id,
                embedding=embedding,
                chunk_text=chunk_obj.chunk_text
            )

        # 6. Update status
        repo.update_document_status(document_id, "completed")
        db.commit()

        print(f"Processed document {document_id}: {len(chunks)} chunks created")

    except Exception as e:
        db.rollback()
        repo.update_document_status(document_id, "failed")
        db.commit()
        print(f"Error processing document {document_id}: {e}")
        raise

    finally:
        db.close()
