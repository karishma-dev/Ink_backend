from app.db.repositories.persona_repository import PersonaRepository

class ToolsService:
    def __init__(self, neo4j_session):
        self.persona_repo = PersonaRepository(neo4j_session)

    def recommend_personas(self, topic: str, limit: int = 5):
        results = self.persona_repo.get_personas_by_topic(topic, limit)
        return results