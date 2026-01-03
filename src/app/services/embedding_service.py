import google.genai as genai
import os

class EmbeddingService:
    """Service for generating text embeddings"""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for a single text"""

        result = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return result.embeddings[0].values

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings