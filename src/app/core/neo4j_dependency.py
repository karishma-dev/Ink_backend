from app.db.neo4j_connection import get_neo4j_session
from fastapi import Depends

def get_neo4j_db():
    session = get_neo4j_session()
    try:
        yield session
    finally: 
        session.close()