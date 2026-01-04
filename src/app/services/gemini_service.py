import google.genai as genai
from google.genai import types
import os
from app.services.tools_service import ToolsService

class GeminiService:
    def __init__(self, tools_service = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.tools_service = tools_service

    def chat(self, message: str, system_prompt: str = None, tools: list = None, history: list = None) -> str:
        """Stream chat response with tool call support"""
        
        # Build config with or without tools
        if self.tools_service:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[self._build_recommend_personas_tool()]
            )
        else:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        
        if history:
            contents = history + [{"role": "user", "parts": [{"text": message}]}]
        else:
            contents = message
            
        response = self.client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
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
                tool_name = tool_call.name
                tool_args = dict(tool_call.args) if tool_call.args else {}

                yield {"type": "tool_call", "name": tool_name, "args": tool_args}

                if tool_name == "recommend_personas" and self.tools_service:
                    tool_result = self.tools_service.recommend_personas(**tool_args)
                    tool_results.append({
                        "name": tool_name,
                        "result": tool_result
                    })
            
            yield {"type": "status", "content": "Processing tool results..."}

            second_config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )

            second_stream = self.client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=[
                    message,
                    {"tool_results": tool_results}
                ],
                config=second_config
            )
        
            for chunk in second_stream:
                if chunk.text:
                    yield {"type": "content", "content": chunk.text}
    
    def _build_recommend_personas_tool(self):
        """Build the recommend_personas tool using proper SDK types"""
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="recommend_personas",
                    description="Find personas matching a specific topic",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "topic": types.Schema(
                                type=types.Type.STRING,
                                description="Topic to search for (e.g., 'business', 'tech', 'creative')"
                            ),
                            "limit": types.Schema(
                                type=types.Type.INTEGER,
                                description="Max personas to return"
                            )
                        },
                        required=["topic"]
                    )
                )
            ]
        )