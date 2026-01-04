"""
Collaboration WebSocket Endpoint

Handles real-time collaboration for draft editing.
Features: presence, cursor sync, content sync (last-write-wins).
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.websocket_manager import manager
from app.core.security import decode_token
from app.db.database import get_db
from app.db.repositories.draft_repository import DraftRepository
from sqlalchemy.orm import Session
import json

collab_router = APIRouter()

async def get_user_from_token(token: str) -> dict:
    """Validate token and get user info"""
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("sub"), "username": payload.get("username", f"User {payload.get('sub')}")}
    except Exception:
        return None

@collab_router.websocket("/ws/draft/{draft_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    draft_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time collaboration on a draft.
    
    Connect with: ws://host/api/collab/ws/draft/{draft_id}?token={jwt_token}
    
    Events from client:
    - {"type": "cursor", "position": 123, "selection_start": 100, "selection_end": 150}
    - {"type": "content", "content": "full document text", "cursor_position": 123}
    - {"type": "ping"}
    
    Events from server:
    - {"type": "room_state", "draft_id": 1, "content": "...", "users": [...], "your_color": "#FF6B6B"}
    - {"type": "user_joined", "user_id": 1, "username": "John", "color": "#FF6B6B", "users": [...]}
    - {"type": "user_left", "user_id": 1, "username": "John", "users": [...]}
    - {"type": "cursor_update", "user_id": 1, "username": "John", "color": "#FF6B6B", "position": 123, ...}
    - {"type": "content_update", "user_id": 1, "username": "John", "content": "...", "cursor_position": 123}
    - {"type": "pong"}
    """
    # Validate token
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = user["user_id"]
    username = user["username"]
    
    # Connect to room
    await manager.connect(websocket, draft_id, user_id, username)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "cursor":
                # Update cursor position
                await manager.update_cursor(
                    user_id=user_id,
                    position=data.get("position", 0),
                    selection_start=data.get("selection_start"),
                    selection_end=data.get("selection_end")
                )
            
            elif msg_type == "content":
                # Update content (last-write-wins)
                await manager.update_content(
                    user_id=user_id,
                    content=data.get("content", ""),
                    cursor_position=data.get("cursor_position")
                )
            
            elif msg_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception as e:
        await manager.disconnect(user_id)
        raise


@collab_router.get("/draft/{draft_id}/presence")
async def get_draft_presence(draft_id: int):
    """
    Get current users viewing/editing a draft (HTTP endpoint).
    Useful for showing presence indicators without WebSocket connection.
    """
    room = manager.rooms.get(draft_id)
    if not room:
        return {"draft_id": draft_id, "users": [], "count": 0}
    
    users = [
        {
            "user_id": session.user_id,
            "username": session.username,
            "color": session.color
        }
        for session in room.users.values()
    ]
    
    return {
        "draft_id": draft_id,
        "users": users,
        "count": len(users)
    }
