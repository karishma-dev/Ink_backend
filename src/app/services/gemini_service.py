import google.genai as genai
import os
from app.services.tools_service import ToolsService

class GeminiService:
    def __init__(self, tools_service = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.tools_service = tools_service

    def chat(self, message: str, system_prompt: str = None, tools: list = None) -> str:
        """Stream chat response with tool call support"""
        tools = self.get_tools() if self.tools_service else None

        config = genai.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools
        )
        
        response = self.client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=message,
            config=config
        )

        collected_text = ""
        tool_calls_found = []

        for chunk in response:
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls_found.append(part.function_call)
            
            if chunk.text:
                collected_text += chunk.text
                yield {"type": "content", "content": chunk.text}

        if tool_calls_found:
            tool_results = []

            for tool_call in tool_calls_found:
                tool_name = tool_call.function_name
                tool_args = dict(tool_call.args) if tool_call.args else {}

                yield {"type": "tool_call", "name": tool_name, "args": tool_args}

                if tool_name == "recommend_personas" and self.tools_service:
                    tool_result = self.tools_service.recommend_personas(**tool_args)
                    tool_results.append({
                        "name": tool_name,
                        "result": tool_result
                    })
            
            yield {"type": "status", "content": "Processing tool results..."}

            second_stream = self.client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=[
                    message,
                    {"tool_results": tool_results}
                ],
                config=config
            )
        
            for chunk in second_stream:
                if chunk.text:
                    yield {"type": "content", "content": chunk.text}
    
    def get_tools(self):
        """Return all available tools for Gemini"""
        return [
            {
                "name": "recommend_personas",
                "description": "Find personas matching a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Topic to search for (e.g., 'business', 'tech', 'creative')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max personas to return",
                            "default": 5
                        }
                    },
                    "required": ["topic"]
                }
            }
        ]