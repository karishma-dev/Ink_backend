from pypdf import PdfReader
from pathlib import Path

class DocumentProcessor:
    """Service for extracting text from uploaded documents"""

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from all pages of a PDF"""
        reader = PdfReader(file_path)

        all_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)

        full_text = "\n".join(all_text)

        if not full_text.strip():
            raise ValueError("PDF appears to be empty or contains only images")

        return full_text

    def extract_text_from_markdown(self, file_path: str) -> str:
        """Extract text from markdown/text files"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_text(self, file_path: str, file_type: str) -> str:
        """Route to the correct extraction method based on file type"""
        if file_type == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type in [".md", ".txt"]:
            return self.extract_text_from_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Split text into overlapping chunks for better RAG retrieval

        Args:
            text: The full document text
            chunk_size: Target size for each chunk (in characters)
            overlap: How much overlap between chunks

        Returns:
            List of text chunks
        """

        if not text:
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - overlap

        return chunks