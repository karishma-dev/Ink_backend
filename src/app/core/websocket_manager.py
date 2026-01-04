"""
WebSocket Connection Manager

Manages WebSocket connections for real-time collaboration.
Handles rooms (one per draft), user presence, and broadcasting.
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class UserSession:
    """Represents a connected user in a room"""
    user_id: int
    username: str
    websocket: WebSocket
    color: str  # Assigned color for cursor
    cursor_position: Optional[int] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Room:
    """Represents a collaboration room (one per draft)"""
    draft_id: int
    users: Dict[int, UserSession] = field(default_factory=dict)
    content: str = ""  # Current document content
    last_updated: datetime = field(default_factory=datetime.utcnow)

class ConnectionManager:
    """Manages WebSocket connections and rooms"""
    
    # Predefined colors for user cursors
    CURSOR_COLORS = [
        "#FF6B6B",  # Red
        "#4ECDC4",  # Teal
        "#45B7D1",  # Blue
        "#96CEB4",  # Green
        "#FFEAA7",  # Yellow
        "#DDA0DD",  # Plum
        "#98D8C8",  # Mint
        "#F7DC6F",  # Gold
    ]
    
    def __init__(self):
        # draft_id -> Room
        self.rooms: Dict[int, Room] = {}
        # user_id -> draft_id (track which room each user is in)
        self.user_rooms: Dict[int, int] = {}
    
    def _get_color(self, room: Room) -> str:
        """Assign a color to a new user based on existing users"""
        used_colors = {user.color for user in room.users.values()}
        for color in self.CURSOR_COLORS:
            if color not in used_colors:
                return color
        # If all colors used, cycle back
        return self.CURSOR_COLORS[len(room.users) % len(self.CURSOR_COLORS)]
    
    async def connect(self, websocket: WebSocket, draft_id: int, user_id: int, username: str):
        """Connect a user to a draft room"""
        await websocket.accept()
        
        # Create room if doesn't exist
        if draft_id not in self.rooms:
            self.rooms[draft_id] = Room(draft_id=draft_id)
        
        room = self.rooms[draft_id]
        color = self._get_color(room)
        
        # Create user session
        session = UserSession(
            user_id=user_id,
            username=username,
            websocket=websocket,
            color=color
        )
        
        # Add to room and track
        room.users[user_id] = session
        self.user_rooms[user_id] = draft_id
        
        # Notify others in room
        await self.broadcast_to_room(draft_id, {
            "type": "user_joined",
            "user_id": user_id,
            "username": username,
            "color": color,
            "users": self._get_room_users(draft_id)
        }, exclude_user=user_id)
        
        # Send current state to joining user
        await websocket.send_json({
            "type": "room_state",
            "draft_id": draft_id,
            "content": room.content,
            "users": self._get_room_users(draft_id),
            "your_color": color
        })
    
    async def disconnect(self, user_id: int):
        """Disconnect a user from their room"""
        if user_id not in self.user_rooms:
            return
        
        draft_id = self.user_rooms[user_id]
        room = self.rooms.get(draft_id)
        
        if room and user_id in room.users:
            username = room.users[user_id].username
            del room.users[user_id]
            del self.user_rooms[user_id]
            
            # Notify others
            await self.broadcast_to_room(draft_id, {
                "type": "user_left",
                "user_id": user_id,
                "username": username,
                "users": self._get_room_users(draft_id)
            })
            
            # Clean up empty rooms
            if not room.users:
                del self.rooms[draft_id]
    
    async def broadcast_to_room(self, draft_id: int, message: dict, exclude_user: int = None):
        """Broadcast message to all users in a room"""
        room = self.rooms.get(draft_id)
        if not room:
            return
        
        for user_id, session in room.users.items():
            if user_id != exclude_user:
                try:
                    await session.websocket.send_json(message)
                except Exception:
                    pass  # Connection might be closed
    
    async def update_cursor(self, user_id: int, position: int, selection_start: int = None, selection_end: int = None):
        """Update a user's cursor position"""
        if user_id not in self.user_rooms:
            return
        
        draft_id = self.user_rooms[user_id]
        room = self.rooms.get(draft_id)
        
        if room and user_id in room.users:
            session = room.users[user_id]
            session.cursor_position = position
            session.selection_start = selection_start
            session.selection_end = selection_end
            
            # Broadcast to others
            await self.broadcast_to_room(draft_id, {
                "type": "cursor_update",
                "user_id": user_id,
                "username": session.username,
                "color": session.color,
                "position": position,
                "selection_start": selection_start,
                "selection_end": selection_end
            }, exclude_user=user_id)
    
    async def update_content(self, user_id: int, content: str, cursor_position: int = None):
        """Update document content (last-write-wins)"""
        if user_id not in self.user_rooms:
            return
        
        draft_id = self.user_rooms[user_id]
        room = self.rooms.get(draft_id)
        
        if room:
            room.content = content
            room.last_updated = datetime.utcnow()
            
            if user_id in room.users:
                session = room.users[user_id]
                
                # Broadcast to others
                await self.broadcast_to_room(draft_id, {
                    "type": "content_update",
                    "user_id": user_id,
                    "username": session.username,
                    "content": content,
                    "cursor_position": cursor_position
                }, exclude_user=user_id)
    
    def _get_room_users(self, draft_id: int) -> list:
        """Get list of users in a room"""
        room = self.rooms.get(draft_id)
        if not room:
            return []
        
        return [
            {
                "user_id": session.user_id,
                "username": session.username,
                "color": session.color,
                "cursor_position": session.cursor_position,
                "selection_start": session.selection_start,
                "selection_end": session.selection_end
            }
            for session in room.users.values()
        ]
    
    def get_room_count(self, draft_id: int) -> int:
        """Get number of users in a room"""
        room = self.rooms.get(draft_id)
        return len(room.users) if room else 0


# Global connection manager instance
manager = ConnectionManager()
