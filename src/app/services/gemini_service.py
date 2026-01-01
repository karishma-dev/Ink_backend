import google.genai as genai
import os

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def chat(self, message: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message
        )
        return response.text