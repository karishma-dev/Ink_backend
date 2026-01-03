from qdrant_client import QdrantClient
from  qdrant_client.models import Distance, VectorParams, PointStruct
import os

class QdrantService:
    """Service for storing and searching document embeddings"""

    COLLECTION_NAME = "document_chunks"
    VECTOR_SIZE = 768 # Gemini text-embedding-004 dimension

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    def store_embedding(self, chunk_id: int, user_id: int, document_id: int, embedding: list[float], chunk_text: str):
        """"Store a single chunk embedding"""
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "user_id": user_id,
                        "document_id": document_id,
                        "chunk_text": chunk_text
                    }
                )
            ]
        )

    def search(self, query_embedding: list[float], user_id: int, limit: int = 5):
        """Search for similar chunks (filtered by user)"""
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {
                        "key": "user_id",
                        "match": {
                            "value": user_id
                        }
                    }
                ]
            },
            limit=limit
        )
        return results

    def search_by_documents(self, query_embedding: list[float], document_ids: list[int], limit: int = 5):
        """Search only within specified documents"""
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {
                        "key": "document_id",
                        "match": {
                            "any": document_ids
                        }
                    }
                ]
            },
            limit=limit
        )
        return results