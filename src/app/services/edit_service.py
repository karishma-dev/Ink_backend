"""
Edit Service

Handles AI-powered document editing.
Generates structured edits that frontend can apply with diff preview.
"""
import google.genai as genai
import os
import json
import re
from typing import Optional
from app.services.prompt_builder import PromptBuilder

class EditService:
    """Service for generating document edits using AI"""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
    
    def generate_edits(
        self, 
        document_content: str, 
        instruction: str,
        selection: dict = None,
        persona: dict = None
    ) -> dict:
        """
        Generate structured edits for a document based on user instruction.
        
        Args:
            document_content: Full document text
            instruction: User's edit instruction
            selection: Optional dict with start, end, text
            persona: Optional persona for style matching
            
        Returns:
            Dict with 'explanation' (str) and 'edits' (list)
        """
        
        # Use PromptBuilder for consistent prompts
        prompt = PromptBuilder.build_edit_prompt(
            document_content=document_content,
            instruction=instruction,
            selection=selection,
            persona=persona
        )
        
        config = genai.GenerateContentConfig(
            temperature=0.3,  # Lower temperature for precise edits
        )
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )
        
        return self._parse_response(response.text, document_content)
    
    def _parse_response(self, response_text: str, document_content: str) -> dict:
        """Parse the response - could be JSON (edit) or plain text (question)"""
        cleaned = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                cleaned = match.group(0)
        
        # Try to parse as JSON (edit response)
        try:
            result = json.loads(cleaned)
            
            # It's a JSON response - this is an edit
            response_type = result.get("type", "edit")
            explanation = result.get("explanation", "Changes applied.")
            edits = result.get("edits", [])
            
            # Validate edits
            valid_edits = []
            for edit in edits:
                if self._validate_edit(edit, document_content):
                    valid_edits.append({
                        "type": edit.get("type", "replace"),
                        "start": edit["start"],
                        "end": edit["end"],
                        "original": edit.get("original", ""),
                        "replacement": edit.get("replacement", "")
                    })
            
            return {
                "response_type": "edit",
                "explanation": explanation,
                "edits": valid_edits
            }
            
        except (json.JSONDecodeError, KeyError):
            # Not JSON - this is a question response (plain text)
            return {
                "response_type": "question",
                "explanation": response_text.strip(),
                "edits": []
            }
    
    def _validate_edit(self, edit: dict, document_content: str) -> bool:
        """Validate that an edit is properly formed"""
        required = ["start", "end"]
        if not all(key in edit for key in required):
            return False
        
        start = edit["start"]
        end = edit["end"]
        
        # Basic bounds check
        if start < 0 or end < 0:
            return False
        if start > end:
            return False
        if end > len(document_content):
            return False
            
        return True
    
    def _fallback_response(self, response_text: str, document_content: str) -> dict:
        """Fallback: replace entire document if JSON parsing fails"""
        return {
            "explanation": "I've rewritten the document based on your request.",
            "edits": [{
                "type": "replace",
                "start": 0,
                "end": len(document_content),
                "original": document_content,
                "replacement": response_text.strip()
            }]
        }
