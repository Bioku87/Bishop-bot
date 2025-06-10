"""
Bishop Bot - Character Management System
Last updated: 2025-05-31 15:29:42 UTC by Bioku87

Handles D&D character registration and lookup for users.
"""
import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Import database manager
from database import db_manager

logger = logging.getLogger('bishop_bot.characters')

class CharacterManager:
    """Manages character data for Bishop Bot"""
    
    def __init__(self):
        """Initialize the character manager"""
        self.characters = {}
        self.data_file = os.path.join("data", "characters", "characters.json")
        self.characters_dir = os.path.join("data", "characters")
        
        # Ensure directories exist
        os.makedirs(self.characters_dir, exist_ok=True)
        
    async def initialize(self):
        """Initialize the character manager"""
        try:
            # Load character data from file and database
            await self.load_characters()
            logger.info("Character manager initialized")
        except Exception as e:
            logger.error(f"Error initializing character manager: {e}")
    
    async def load_characters(self):
        """Load characters from storage"""
        # Load from JSON file first
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.characters = data.get('characters', {})
                    logger.info(f"Loaded {len(self.characters)} characters from file")
            except Exception as e:
                logger.error(f"Error loading characters from file: {e}")
        
        # Then load/sync with database
        try:
            db_characters = await db_manager.get_all_characters()
            
            for char in db_characters:
                user_id = char["user_id"]
                
                # Add to in-memory cache if not present
                if user_id not in self.characters:
                    self.characters[user_id] = {
                        "user_id": user_id,
                        "username": char["username"],
                        "character_name": char["character_name"],
                        "race": char["race"],
                        "class": char["character_class"],
                        "subclass": char["sub_class"],
                        "real_name": char["real_name"],
                        "created_at": char["created_at"],
                        "updated_at": char["updated_at"]
                    }
        except Exception as e:
            logger.error(f"Error loading characters from database: {e}")
    
    async def save_characters(self):
        """Save characters to file"""
        try:
            data = {
                'version': 1,
                'last_updated': datetime.now().isoformat(),
                'characters': self.characters
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.characters)} characters to file")
            return True
        except Exception as e:
            logger.error(f"Error saving characters to file: {e}")
            return False
    
    async def register_character(self, user_id: str, username: str, character_data: Dict[str, Any]) -> bool:
        """Register a character for a user"""
        try:
            # Format character data
            now = datetime.now().isoformat()
            character = {
                "user_id": user_id,
                "username": username,
                "character_name": character_data.get("character_name", "Unknown"),
                "race": character_data.get("race"),
                "class": character_data.get("class"),
                "subclass": character_data.get("subclass"),
                "real_name": character_data.get("real_name"),
                "created_at": now,
                "updated_at": now
            }
            
            # Add to in-memory cache
            self.characters[user_id] = character
            
            # Save to file
            await self.save_characters()
            
            # Save to database
            await db_manager.create_character(
                user_id=user_id,
                username=username,
                character_name=character["character_name"],
                race=character["race"],
                character_class=character["class"],
                sub_class=character["subclass"],
                real_name=character["real_name"]
            )
            
            logger.info(f"Registered character for {username}: {character['character_name']}")
            return True
        except Exception as e:
            logger.error(f"Error registering character: {e}")
            return False
    
    async def get_character(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a character by user ID"""
        # Check in-memory cache first
        if user_id in self.characters:
            return self.characters[user_id]
            
        # Check database
        try:
            character = await db_manager.get_character(user_id)
            
            if character:
                # Add to cache
                self.characters[user_id] = {
                    "user_id": character["user_id"],
                    "username": character["username"],
                    "character_name": character["character_name"],
                    "race": character["race"],
                    "class": character["character_class"],
                    "subclass": character["sub_class"],
                    "real_name": character["real_name"],
                    "created_at": character["created_at"],
                    "updated_at": character["updated_at"]
                }
                
                return self.characters[user_id]
        except Exception as e:
            logger.error(f"Error getting character from database: {e}")
            
        return None
    
    async def get_character_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a character by username"""
        # Check in-memory cache first
        for char in self.characters.values():
            if char["username"].lower() == username.lower():
                return char
                
        # Check database
        try:
            character = await db_manager.get_character_by_username(username)
            
            if character:
                # Add to cache
                user_id = character["user_id"]
                self.characters[user_id] = {
                    "user_id": user_id,
                    "username": character["username"],
                    "character_name": character["character_name"],
                    "race": character["race"],
                    "class": character["character_class"],
                    "subclass": character["sub_class"],
                    "real_name": character["real_name"],
                    "created_at": character["created_at"],
                    "updated_at": character["updated_at"]
                }
                
                return self.characters[user_id]
        except Exception as e:
            logger.error(f"Error getting character from database: {e}")
            
        return None
    
    async def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """Get all characters"""
        # Refresh from database to ensure we have the latest
        await self.load_characters()
        return self.characters
    
    async def update_character(self, user_id: str, character_data: Dict[str, Any]) -> bool:
        """Update a character"""
        # Check if character exists
        existing_character = await self.get_character(user_id)
        
        if not existing_character:
            logger.warning(f"Cannot update non-existent character for user {user_id}")
            return False
            
        try:
            # Update character data
            now = datetime.now().isoformat()
            
            character = {
                **existing_character,
                **character_data,
                "updated_at": now
            }
            
            # Update in-memory cache
            self.characters[user_id] = character
            
            # Save to file
            await self.save_characters()
            
            # Update in database
            db_data = {
                "character_name": character["character_name"],
                "race": character["race"],
                "character_class": character["class"],
                "sub_class": character["subclass"],
                "real_name": character["real_name"],
            }
            
            await db_manager.update_character(user_id, db_data)
            
            logger.info(f"Updated character for user {user_id}: {character['character_name']}")
            return True
        except Exception as e:
            logger.error(f"Error updating character: {e}")
            return False
    
    async def delete_character(self, user_id: str) -> bool:
        """Delete a character"""
        if user_id not in self.characters:
            logger.warning(f"Cannot delete non-existent character for user {user_id}")
            return False
            
        try:
            # Remove from in-memory cache
            character = self.characters.pop(user_id)
            
            # Save to file
            await self.save_characters()
            
            # Delete from database
            await db_manager.delete_character(user_id)
            
            logger.info(f"Deleted character for user {user_id}: {character['character_name']}")
            return True
        except Exception as e:
            logger.error(f"Error deleting character: {e}")
            return False

# Create singleton instance
character_manager = CharacterManager()