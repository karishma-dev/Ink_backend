"""
Autocomplete Service

Provides intelligent text completion suggestions using Gemini.
Supports persona-aware completions for consistent writing style.
"""
import google.genai as genai
from google.genai import types
import os
from typing import Optional
from app.services.prompt_builder import PromptBuilder

class AutocompleteService:
    """Service for generating autocomplete suggestions"""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
    
    def get_suggestion(self, context: str, persona: dict = None, max_tokens: int = 50) -> str:
        """Generate autocomplete suggestion for the given context"""
        
        # Use PromptBuilder for consistent prompts
        prompt = PromptBuilder.build_autocomplete_prompt(context, persona)
        
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,  # Slightly creative but not too random
        )
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )
        
        return response.text.strip() if response.text else ""
    
    def get_suggestion_stream(self, context: str, persona: dict = None, max_tokens: int = 50):
        """Stream autocomplete suggestion for the given context"""
        
        # Use PromptBuilder for consistent prompts
        prompt = PromptBuilder.build_autocomplete_prompt(context, persona)
        
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )
        
        for chunk in self.client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        ):
            if chunk.text:
                yield chunk.text
