class PromptBuilder:
    
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