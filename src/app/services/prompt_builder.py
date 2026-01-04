class PromptBuilder:
    BASE_SYSTEM_PROMPT = """You are an expert AI writing assistant designed to help users with their writing projects.

    ## Your Core Capabilities:
    - Help users brainstorm ideas, outlines, and titles
    - Assist with drafting, editing, and refining content
    - Provide suggestions while maintaining the user's voice
    - Answer questions about writing, style, and content

    ## Your Behavior:
    - Be collaborative, not prescriptive — suggest, don't dictate
    - Ask clarifying questions when the user's intent is unclear
    - Maintain consistency with any persona or style the user has defined
    - Be concise unless the user asks for detailed explanations

    ## When Using Reference Documents:
    - If documents are provided, use them to inform your responses
    - When you use information from a document, cite it using brackets: [1], [2], etc.
    - Only cite when you actually use information from that source
    - Be transparent about what comes from documents vs. your own knowledge

    ## Guidelines:
    - Never make up facts or citations — if you don't know, say so
    - Respect the user's creative choices even if you'd do it differently
    - Keep responses focused and actionable
    """

    @staticmethod
    def build_full_prompt(persona: dict = None, document_context: str = None) -> str:
        """Build complete system prompt with optional persona and documents"""

        prompt_parts = [PromptBuilder.BASE_SYSTEM_PROMPT]

        # Add persona if provided
        if persona:
            persona_prompt = PromptBuilder.build_persona_prompt(persona)
            prompt_parts.append(f"\n## Active Writing Persona:\n{persona_prompt}")

        if document_context:
            prompt_parts.append(f"\n## Reference Documents:\n{document_context}")

        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_edit_prompt(document_content: str, instruction: str, selection: dict = None, persona: dict = None) -> str:
        """Build prompt for document editing mode"""
        
        base = PromptBuilder.BASE_SYSTEM_PROMPT
        
        edit_instructions = """
## Editor Context Mode:
You are helping a user who is writing a document. They may ask questions OR request edits.

**FIRST, determine the user's intent:**
- If they're asking a QUESTION (advice, feedback, suggestions), respond with normal conversational text.
- If they're requesting an EDIT or CREATION, respond with the JSON format below.

**For QUESTIONS/ADVICE** (e.g., "How should I improve this?", "Is this intro good?", "What do you think?"):
Just respond naturally with helpful text. No JSON needed.

**For EDIT/CREATE REQUESTS** (e.g., "Make this shorter", "Write an email", "Create a paragraph about X", "Add a conclusion", "Draft a message"):
Return a JSON object. For CREATING new content when document is empty or for insertions, use start:0, end:0:
{
  "type": "edit",
  "explanation": "I created the email draft for you.",
  "edits": [
    {
      "type": "replace",
      "start": <start character position (use 0 for new content)>,
      "end": <end character position (use 0 for insertions, or document length for full replacement)>,
      "original": "<exact text being replaced, or empty for insertions>",
      "replacement": "<new text>"
    }
  ]
}

IMPORTANT:
- "Write", "Create", "Draft", "Generate" = EDIT REQUEST (return JSON with content in edits)
- "How should I", "What do you think", "Is this good" = QUESTION (return text)
- For questions: Just respond with text, no JSON
- For edits/creations: Respond with ONLY the JSON object, no markdown code blocks
- If inserting new content at beginning: use start:0, end:0
- If replacing entire document: use start:0, end:<document length>
- If user requests an edit but no changes are needed: {"type": "edit", "explanation": "The document looks good as is!", "edits": []}
"""
        
        selection_context = ""
        if selection:
            selection_context = f"""
## User's Selection (characters {selection.get('start', 0)} to {selection.get('end', 0)}):
---
{selection.get('text', '')}
---
Focus your edits on this selection.
"""
        
        persona_context = ""
        if persona:
            persona_context = f"""
## Writing Style:
- Formality: {persona.get('formality_level', 5)}/10
- Persona: {persona.get('name', 'Default')}
"""
        
        return f"""{base}
{edit_instructions}
{selection_context}
{persona_context}
## Document Content:
---
{document_content}
---

## User Instruction: {instruction}
"""

    @staticmethod
    def build_autocomplete_prompt(context: str, persona: dict = None) -> str:
        """Build prompt for autocomplete/Smart Compose"""
        
        base = PromptBuilder.BASE_SYSTEM_PROMPT
        
        autocomplete_instructions = """
## Autocomplete Mode:
Provide ONLY the completion text - the words that come AFTER the user's text.

CRITICAL RULES:
- Output ONLY new words that continue the text
- NEVER repeat ANY part of the existing text
- Start your response immediately with the next word
- Keep it to 1 sentence (10-30 words)
- No quotes, no explanations, just the completion

Example:
User's text: "I am writing to inform you that"
CORRECT output: "the project has been completed ahead of schedule."
WRONG output: "I am writing to inform you that the project has been completed."
"""
        
        persona_context = ""
        if persona:
            persona_context = f"""
## Writing Style to Match:
- Formality: {persona.get('formality_level', 5)}/10
- Creativity: {persona.get('creativity_level', 5)}/10
- Sentence style: {persona.get('sentence_length', 'medium')}
- Persona: {persona.get('name', 'Default')}
"""
        
        return f"""{base}
{autocomplete_instructions}
{persona_context}
## Complete this text (provide ONLY the next words):
{context}"""
    
    @staticmethod
    def build_persona_prompt(persona:dict) -> str:
        """
        Takes persona data and returns a system prompt string for Gemini

        Args:
            persona: dict with persona details (name, samples,formality_level, etc.)

        Returns:
            str: A system prompt that instructs Gemini to write in this persona's voice
        """

        prompt = f"""You are writing as the persona: {persona['name']}
        Description: {persona['description']}

        Writing style:
        - Formality Level: {persona['formality_level']}/10
        - Creativity Level: {persona['creativity_level']}/10
        - Sentence Length: {persona['sentence_length']}
        - Use Metaphors: {persona['use_metaphors']}
        - Jargon Level: {persona['jargon_level']}/10

        Examples of this voice:
        {PromptBuilder.format_samples(persona['samples'])}

        Topics to focus on: {', '.join(persona['topics'])}
        Audience: {persona['audience']}
        Purpose: {persona['purpose']}

        Words to NEVER use: {', '.join(persona['banned_words']) if persona['banned_words'] else 'None'}
        
        Now, write in this voice:
        """

        return prompt
    
    @staticmethod
    def format_samples(samples: list) -> str:
        """Helper to format samples nicely"""
        return "\n".join([f"- {sample}" for sample in samples])