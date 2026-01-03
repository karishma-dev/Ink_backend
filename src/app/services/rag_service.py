from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

class RAGService:
    """Service for Retrieval-Augmented Generation"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()

    def get_relevant_context(self, query: str, document_ids: list[int], limit: int = 5) -> str:
        """Get relevant document chunks for a query, with citation metadata"""

        if not document_ids:
            return {"context": "", "citations": []}

        # 1. Embed the query
        query_embedding = self.embedding_service.generate_embedding(query)

        # 2. Search selected documents
        results = self.qdrant_service.search_by_documents(query_embedding, document_ids, limit)

        if not results:
            return {"context": "", "citations": []}

        # 3. Build context string with citation markers AND citations list
        context_parts = []
        citations = []

        for i, result in enumerate(results, start=1):
            citation_marker = f"[{i}]"
            chunk_text = result.payload["chunk_text"]

            # Add to context with marker
            context_parts.append(f"{citation_marker} {chunk_text}")

            # Add to citations list
            citations.append({
                "index": i,
                "document_id": result.payload["document_id"],
                "chunk_text": chunk_text,
                "score": result.score
            })

        context = "\n\n".join(context_parts)
        return {
            "context": context,
            "citations": citations
        }