import google.genai as genai
import os

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def chat(self, message: str, system_prompt: str = None) -> str:
        config = None
        if system_prompt:
            config = genai.GenerateContentConfig(
                system_instruction=system_prompt
            )
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message,
            config=config
        )
        return response.text