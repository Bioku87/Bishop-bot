"""
Bishop Bot - Database Manager
Last updated: 2025-05-31 15:23:46 UTC by Bioku87

Handles database operations for the bot.
"""
import os
import json
import logging
import sqlite3
import asyncio
import aiosqlite
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger('bishop_bot.database')

class DatabaseManager:
    """Manages database operations for Bishop Bot"""
    
    def __init__(self, db_path="data/bishop.db"):
        """Initialize the database manager"""
        self.db_path = db_path
        self.connection = None
        self.initialized = False
        
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    async def initialize(self):
        """Initialize the database connection and tables"""
        if self.initialized:
            return
            
        try:
            # Create connection
            self.connection = await aiosqlite.connect(self.db_path)
            
            # Create tables
            await self._create_tables()
            
            self.initialized = True
            logger.info(f"Database initialized: {self.db_path}")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def close(self):
        """Close the database connection"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.initialized = False
            
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        if not self.connection:
            raise RuntimeError("Database not initialized")
            
        # Characters table
        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            character_name TEXT,
            race TEXT,
            character_class TEXT,
            sub_class TEXT,
            real_name TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        # Voice profiles table
        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS voice_profiles (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'en-US',
            accent TEXT,
            gender TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        # Transcripts table
        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS transcripts (
            id TEXT PRIMARY KEY,
            name TEXT,
            date TEXT,
            duration INTEGER,
            line_count INTEGER,
            speakers TEXT,
            text TEXT,
            metadata TEXT
        )
        ''')
        
        # Commit changes
        await self.connection.commit()
        
    # Character operations
    
    async def create_character(self, user_id: str, username: str, character_name: str, 
                              race: str = None, character_class: str = None,
                              sub_class: str = None, real_name: str = None) -> bool:
        """Create a new character entry"""
        if not self.initialized:
            await self.initialize()
            
        try:
            now = datetime.now().isoformat()
            
            await self.connection.execute('''
            INSERT OR REPLACE INTO characters
            (user_id, username, character_name, race, character_class, sub_class, real_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, character_name, race, character_class, 
                sub_class, real_name, now, now
            ))
            
            await self.connection.commit()
            logger.info(f"Created character for user {username}: {character_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating character: {e}")
            return False
    
    async def get_character(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a character by user ID"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM characters WHERE user_id = ?', 
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "character_name": row[2],
                        "race": row[3],
                        "character_class": row[4],
                        "sub_class": row[5],
                        "real_name": row[6],
                        "created_at": row[7],
                        "updated_at": row[8]
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting character: {e}")
            return None
    
    async def get_character_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a character by username"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM characters WHERE username = ?', 
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "character_name": row[2],
                        "race": row[3],
                        "character_class": row[4],
                        "sub_class": row[5],
                        "real_name": row[6],
                        "created_at": row[7],
                        "updated_at": row[8]
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting character by username: {e}")
            return None
    
    async def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all characters"""
        if not self.initialized:
            await self.initialize()
            
        try:
            characters = []
            
            async with self.connection.execute('SELECT * FROM characters') as cursor:
                async for row in cursor:
                    characters.append({
                        "user_id": row[0],
                        "username": row[1],
                        "character_name": row[2],
                        "race": row[3],
                        "character_class": row[4],
                        "sub_class": row[5],
                        "real_name": row[6],
                        "created_at": row[7],
                        "updated_at": row[8]
                    })
                    
            return characters
            
        except Exception as e:
            logger.error(f"Error getting all characters: {e}")
            return []
    
    async def update_character(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Update a character"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get existing character
            character = await self.get_character(user_id)
            if not character:
                return False
                
            # Update fields
            now = datetime.now().isoformat()
            
            await self.connection.execute('''
            UPDATE characters SET
                username = ?,
                character_name = ?,
                race = ?,
                character_class = ?,
                sub_class = ?,
                real_name = ?,
                updated_at = ?
            WHERE user_id = ?
            ''', (
                data.get("username", character["username"]),
                data.get("character_name", character["character_name"]),
                data.get("race", character["race"]),
                data.get("character_class", character["character_class"]),
                data.get("sub_class", character["sub_class"]),
                data.get("real_name", character["real_name"]),
                now,
                user_id
            ))
            
            await self.connection.commit()
            logger.info(f"Updated character for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return False
    
    async def delete_character(self, user_id: str) -> bool:
        """Delete a character"""
        if not self.initialized:
            await self.initialize()
            
        try:
            await self.connection.execute('DELETE FROM characters WHERE user_id = ?', (user_id,))
            await self.connection.commit()
            logger.info(f"Deleted character for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting character: {e}")
            return False
            
    # Voice profile operations
    
    async def create_voice_profile(self, user_id: str, username: str, language: str = "en-US",
                                 accent: str = None, gender: str = None) -> bool:
        """Create a new voice profile"""
        if not self.initialized:
            await self.initialize()
            
        try:
            now = datetime.now().isoformat()
            
            await self.connection.execute('''
            INSERT OR REPLACE INTO voice_profiles
            (user_id, username, language, accent, gender, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, language, accent, gender, now, now
            ))
            
            await self.connection.commit()
            logger.info(f"Created voice profile for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            return False
    
    async def get_voice_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a voice profile by user ID"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM voice_profiles WHERE user_id = ?', 
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "language": row[2],
                        "accent": row[3],
                        "gender": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting voice profile: {e}")
            return None
    
    async def get_voice_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a voice profile by username"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM voice_profiles WHERE username = ?', 
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "language": row[2],
                        "accent": row[3],
                        "gender": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting voice profile by username: {e}")
            return None
    
    async def get_all_voice_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all voice profiles"""
        if not self.initialized:
            await self.initialize()
            
        try:
            profiles = {}
            
            async with self.connection.execute('SELECT * FROM voice_profiles') as cursor:
                async for row in cursor:
                    profiles[row[0]] = {
                        "user_id": row[0],
                        "username": row[1],
                        "language": row[2],
                        "accent": row[3],
                        "gender": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                    
            return profiles
            
        except Exception as e:
            logger.error(f"Error getting all voice profiles: {e}")
            return {}
    
    async def update_voice_profile(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Update a voice profile"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get existing profile
            profile = await self.get_voice_profile(user_id)
            if not profile:
                return False
                
            # Update fields
            now = datetime.now().isoformat()
            
            await self.connection.execute('''
            UPDATE voice_profiles SET
                username = ?,
                language = ?,
                accent = ?,
                gender = ?,
                updated_at = ?
            WHERE user_id = ?
            ''', (
                data.get("username", profile["username"]),
                data.get("language", profile["language"]),
                data.get("accent", profile["accent"]),
                data.get("gender", profile["gender"]),
                now,
                user_id
            ))
            
            await self.connection.commit()
            logger.info(f"Updated voice profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating voice profile: {e}")
            return False
    
    async def delete_voice_profile(self, user_id: str) -> bool:
        """Delete a voice profile"""
        if not self.initialized:
            await self.initialize()
            
        try:
            await self.connection.execute('DELETE FROM voice_profiles WHERE user_id = ?', (user_id,))
            await self.connection.commit()
            logger.info(f"Deleted voice profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting voice profile: {e}")
            return False
            
    # Transcript operations
    
    async def save_transcript(self, transcript_id: str, name: str, text: str, 
                            date: str = None, duration: int = 0, 
                            line_count: int = 0, speakers: List[str] = None,
                            metadata: Dict[str, Any] = None) -> bool:
        """Save a transcript"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Format data
            if not date:
                date = datetime.now().isoformat()
                
            speakers_json = json.dumps(speakers or [])
            metadata_json = json.dumps(metadata or {})
            
            await self.connection.execute('''
            INSERT OR REPLACE INTO transcripts
            (id, name, date, duration, line_count, speakers, text, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transcript_id, name, date, duration, 
                line_count, speakers_json, text, metadata_json
            ))
            
            await self.connection.commit()
            logger.info(f"Saved transcript: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            return False
    
    async def get_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get a transcript by ID"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM transcripts WHERE id = ?', 
                (transcript_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "date": row[2],
                        "duration": row[3],
                        "line_count": row[4],
                        "speakers": json.loads(row[5]) if row[5] else [],
                        "text": row[6],
                        "metadata": json.loads(row[7]) if row[7] else {}
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            return None
    
    async def get_transcript_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a transcript by name"""
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.connection.execute(
                'SELECT * FROM transcripts WHERE name = ?', 
                (name,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "date": row[2],
                        "duration": row[3],
                        "line_count": row[4],
                        "speakers": json.loads(row[5]) if row[5] else [],
                        "text": row[6],
                        "metadata": json.loads(row[7]) if row[7] else {}
                    }
                    
                return None
                
        except Exception as e:
            logger.error(f"Error getting transcript by name: {e}")
            return None
    
    async def get_all_transcripts(self) -> List[Dict[str, Any]]:
        """Get all transcripts"""
        if not self.initialized:
            await self.initialize()
            
        try:
            transcripts = []
            
            async with self.connection.execute('SELECT * FROM transcripts') as cursor:
                async for row in cursor:
                    transcripts.append({
                        "id": row[0],
                        "name": row[1],
                        "date": row[2],
                        "duration": row[3],
                        "line_count": row[4],
                        "speakers": json.loads(row[5]) if row[5] else [],
                        "metadata": json.loads(row[7]) if row[7] else {}
                    })
                    
            return transcripts
            
        except Exception as e:
            logger.error(f"Error getting all transcripts: {e}")
            return []
    
    async def delete_transcript(self, transcript_id: str) -> bool:
        """Delete a transcript"""
        if not self.initialized:
            await self.initialize()
            
        try:
            await self.connection.execute('DELETE FROM transcripts WHERE id = ?', (transcript_id,))
            await self.connection.commit()
            logger.info(f"Deleted transcript {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting transcript: {e}")
            return False
    
    async def delete_transcript_by_name(self, name: str) -> bool:
        """Delete a transcript by name"""
        if not self.initialized:
            await self.initialize()
            
        try:
            await self.connection.execute('DELETE FROM transcripts WHERE name = ?', (name,))
            await self.connection.commit()
            logger.info(f"Deleted transcript '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting transcript by name: {e}")
            return False

# Create singleton instance
db_manager = DatabaseManager()