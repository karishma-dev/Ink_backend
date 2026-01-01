class PersonaRepository:
    def __init__(self, neo4j_session):
        self.session = neo4j_session

    def create_persona(self, user_id: int, persona_data: dict) -> dict:
        # Create Persona node
        # Connect to User with owns_persona relationship
        # Create BannedWord, Topic, Audience nodes and relationships
        pass

    def get_persona(self, persona_id: int) -> dict:
        # Fetch one persona by id with all relationships
        pass

    def get_user_personas(self, user_id: int) -> dict:
        # Fetch all personas for a user with relationships
        pass

    def update_persona(self, persona_id: int, persona_data: dict) -> dict:
        # Update Persona node and its relationships
        pass

    def delete_persona(self, persona_id: int) -> bool:
        # Delete Persona node and its relationships
        pass