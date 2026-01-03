import google.genai as genai
import os
from app.services.tools_service import ToolsService

class GeminiService:
    def __init__(self, tools_service = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.tools_service = tools_service

    def chat(self, message: str, system_prompt: str = None, tools: list = None) -> str:
        tools = self.get_tools() if self.tools_service else None

        config = genai.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools
        )
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message,
            config=config
        )

        final_response = response
        if response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.function_name
                tool_args = tool_call.args

                if tool_name == "recommend_personas":
                    tool_result = self.tools_service.recommend_personas(**tool_args)
                    tool_results.append({
                        "name": tool_name,
                        "result": tool_result
                    })

            final_response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    message,
                    tool_results
                ],
                config=config
            )
        
        return final_response.text
    
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