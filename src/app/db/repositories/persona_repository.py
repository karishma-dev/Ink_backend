from datetime import datetime 

class PersonaRepository:
    def __init__(self, neo4j_session):
        self.session = neo4j_session

    def create_persona(self, user_id: int, persona_data: dict) -> dict:
        """Create a new persona for a user with all relationships"""

        query = """
        MATCH (u:User {id: $user_id})
        CREATE (p:Persona {
            id: randomUuid(),
            name: $name,
            description: $description,
            samples: $samples,
            formality_level: $formality_level,
            creativity_level: $creativity_level,
            sentence_length: $sentence_length,
            use_metaphors: $use_metaphors,
            jargon_level: $jargon_level,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (u)-[:owns_persona]->(p)
        WITH p
        CREATE (a:Audience {type: $audience})
        CREATE (p)-[:targets_audience]->(a)
        WITH p
        CREATE (pur:Purpose {type: $purpose})
        CREATE (p)-[:for_purpose]->(pur)
        WITH p, $topics as topics, $banned_words as banned_words
        UNWIND topics AS topic
        CREATE (t:Topic {name: topic})
        CREATE (p)-[:targets_topic]->(t)
        WITH p, banned_words
        UNWIND banned_words AS word
        CREATE (bw:BannedWord {text: word})
        CREATE (p)-[:bans_word]->(bw)
        WITH p
        OPTIONAL MATCH (p)-[:targets_topic]->(t:Topic)
        OPTIONAL MATCH (p)-[:bans_word]->(bw:BannedWord)
        OPTIONAL MATCH (p)-[:targets_audience]->(a:Audience)
        OPTIONAL MATCH (p)-[:for_purpose]->(pur:Purpose)
        RETURN p, collect(t.name) as topics, collect(bw.text) as banned_words,
               a.type as audience, pur.type as purpose
        """

        result = self.session.run(query, {
            "user_id": user_id,
            "name": persona_data.get("name"),
            "description": persona_data.get("description"),
            "samples": persona_data.get("samples", []),
            "formality_level": persona_data.get("formality_level"),
            "creativity_level": persona_data.get("creativity_level"),
            "sentence_length": persona_data.get("sentence_length"),
            "use_metaphors": persona_data.get("use_metaphors"),
            "jargon_level": persona_data.get("jargon_level"),
            "audience": persona_data.get("audience"),
            "purpose": persona_data.get("purpose"),
            "topics": persona_data.get("topics", []),
            "banned_words": persona_data.get("banned_words", [])
        })
        
        record = result.single()
        if record:
            persona = self._persona_to_dict(record["p"])
            persona["topics"] = record["topics"] or []
            persona["banned_words"] = record["banned_words"] or []
            persona["audience"] = record["audience"] or ""
            persona["purpose"] = record["purpose"] or ""
            return persona
        return None

    def get_persona(self, persona_id: int) -> dict:
        """Fetch one persona by ID with all relationships"""
        query = """
        MATCH (p:Persona {id: $persona_id})
        OPTIONAL MATCH (p)-[:targets_topic]->(t:Topic)
        OPTIONAL MATCH (p)-[:bans_word]->(bw:BannedWord)
        OPTIONAL MATCH (p)-[:targets_audience]->(a:Audience)
        OPTIONAL MATCH (p)-[:for_purpose]->(pur:Purpose)
        RETURN p, collect(t.name) as topics, collect(bw.text) as banned_words,
               a.type as audience, pur.type as purpose
        """

        result = self.session.run(query,{
            "persona_id": persona_id
        })
        record = result.single()

        if record:
            persona = self._persona_to_dict(record["p"])
            persona["topics"] = record["topics"]
            persona["banned_words"] = record["banned_words"]
            persona["audience"] = record["audience"]
            persona["purpose"] = record["purpose"]
            return persona
        return None

    def get_user_personas(self, user_id: int) -> dict:
        """Fetch all personas for a user"""
        query = """
        MATCH (u:User {id: $user_id})-[:owns_persona]->(p:Persona)
        OPTIONAL MATCH (p)-[:targets_topic]->(t:Topic)
        OPTIONAL MATCH (p)-[:bans_word]->(bw:BannedWord)
        OPTIONAL MATCH (p)-[:targets_audience]->(a:Audience)
        OPTIONAL MATCH (p)-[:for_purpose]->(pur:Purpose)
        RETURN p, collect(DISTINCT t.name) as topics,
               collect(DISTINCT bw.text) as banned_words,
               a.type as audience, pur.type as purpose
        """

        result = self.session.run(query, {"user_id": user_id})
        personas = []

        for record in result:
            persona = self._persona_to_dict(record["p"])
            persona["topics"] = record["topics"] or []
            persona["banned_words"] = record["banned_words"] or []
            persona["audience"] = record["audience"] or ""
            persona["purpose"] = record["purpose"] or ""
            personas.append(persona)

        return personas

    def update_persona(self, persona_id: int, persona_data: dict) -> dict:
        """Update persona properties"""
        set_clauses = []
        params = {"persona_id": persona_id, "updated_at": datetime.utcnow.isoformat()}

        for key, value in persona_data.items():
            if key not in ["topics", "banned_words", "audience", "purpose", "samples"]:
                set_clauses.append(f"p.{key} = ${key}")
                params[key] = value

        set_clauses.append("p.updated_at = $updated_at")
        set_clauses_str = ", ".join(set_clauses)

        query = f"""
        MATCH (p:Persona {{id: $persona_id}})
        SET {set_clauses_str}
        RETURN p
        """

        result = self.session.run(query, params)
        record = result.single()

        if record:
            return self.get_persona(persona_id)
        return None

    def delete_persona(self, persona_id: int) -> bool:
        """Delete persona and all relationships"""
        query = """
        MATCH (p:Persona {id: $persona_id})
        DETACH DELETE p
        """

        self.session.run(query, {"persona_id": persona_id})
        return True

    def _persona_to_dict(self, node) -> dict:
        """Convert Neo4j node to dictionary with proper formatting"""
        data = dict(node)
        # Convert Neo4j DateTime objects to ISO format strings
        if "created_at" in data and data["created_at"] is not None:
            data["created_at"] = str(data["created_at"])
        if "updated_at" in data and data["updated_at"] is not None:
            data["updated_at"] = str(data["updated_at"])
        # Convert UUID id to string if it's not already
        if "id" in data and data["id"] is not None:
            data["id"] = str(data["id"])
        return data
    
    def get_personas_by_topic(self,topic: str, limit: int = 5):
        """Get personas by topic"""
        query = """
        MATCH (p:Persona)-[:targets_topic]->(t:Topic {name: $topic})
        OPTIONAL MATCH (p)-[:targets_topic]->(t2:Topic)
        OPTIONAL MATCH (p)-[:bans_word]->(bw:BannedWord)
        OPTIONAL MATCH (p)-[:targets_audience]->(a:Audience)
        OPTIONAL MATCH (p)-[:for_purpose]->(pur:Purpose)
        RETURN p, collect(DISTINCT t2.name) as topics,
               collect(DISTINCT bw.text) as banned_words,
               a.type as audience, pur.type as purpose
        LIMIT $limit
        """

        result = self.session.run(query, {"topic": topic, "limit": limit})
        personas = []

        for record in result:
            persona = self._persona_to_dict(record["p"])
            persona["topics"] = record["topics"] or []
            persona["banned_words"] = record["banned_words"] or []
            persona["audience"] = record["audience"] or ""
            persona["purpose"] = record["purpose"] or ""
            personas.append(persona)

        return personas