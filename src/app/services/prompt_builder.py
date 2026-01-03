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
    def build_persona_prompt(persona:dict) -> str:
        """
        Takes persona data and returns a system prompt string for Gemini

        Args:
            persona: dict with persona details (name, samples,formality_level, etc.)

        Returns:
            str: A system prompt that instructs Gemini to write in this persona's voice
        """

        # Build the prompt using persona fileds
        # Think about what instructions to give Gemini:
        # - Show examples from samples
        # - Ban certain words
        # - Set tone/formality level
        # - Include topics focus
        # - Set purpose

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