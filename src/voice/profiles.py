"""
Bishop Bot - Voice Profile Manager
Last updated: 2025-05-31 15:29:42 UTC by Bioku87

This module manages user voice profiles for better transcription.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import database manager
from database import db_manager

logger = logging.getLogger('bishop_bot.voice.profiles')

class VoiceProfileManager:
    """Manages voice profiles for users"""
    
    def __init__(self):
        """Initialize the voice profile manager"""
        self.profiles = {}
        self.profile_dir = os.path.join("data", "voice", "profiles")
        self.profile_file = os.path.join(self.profile_dir, "profiles.json")
        
        # Create directories if they don't exist
        os.makedirs(self.profile_dir, exist_ok=True)
        
        logger.info("Voice profile manager initialized")
        
    async def initialize(self):
        """Load profiles from storage"""
        # Load from file
        await self._load_profiles()
        
        # Load from database and sync
        await self._sync_with_database()
        
    async def _load_profiles(self):
        """Load profiles from file"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profiles = data.get('profiles', {})
                    
                logger.info(f"Loaded {len(self.profiles)} voice profiles from file")
            except Exception as e:
                logger.error(f"Error loading voice profiles: {e}")
                self.profiles = {}
        else:
            self.profiles = {}
            
    async def _save_profiles(self):
        """Save profiles to file"""
        try:
            data = {
                'version': 1,
                'last_updated': datetime.now().isoformat(),
                'profiles': self.profiles
            }
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(self.profiles)} voice profiles")
            return True
        except Exception as e:
            logger.error(f"Error saving voice profiles: {e}")
            return False
            
    async def _sync_with_database(self):
        """Sync profiles with database"""
        try:
            # Get profiles from database
            db_profiles = await db_manager.get_all_voice_profiles()
            
            # Update in-memory profiles
            for user_id, profile in db_profiles.items():
                if user_id not in self.profiles:
                    # Add to in-memory profiles
                    self.profiles[user_id] = {
                        'username': profile['username'],
                        'language': profile['language'],
                        'accent': profile['accent'],
                        'gender': profile['gender'],
                        'created_at': profile['created_at'],
                        'updated_at': profile['updated_at']
                    }
            
            # Save updates back to file
            await self._save_profiles()
            
        except Exception as e:
            logger.error(f"Error syncing profiles with database: {e}")
            
    async def create_profile(self, user_id: str, username: str, language: str = 'en-US', 
                           accent: str = None, gender: str = None) -> bool:
        """Create a voice profile for a user"""
        try:
            now = datetime.now().isoformat()
            
            # Create profile
            self.profiles[user_id] = {
                'username': username,
                'language': language,
                'accent': accent,
                'gender': gender,
                'created_at': now,
                'updated_at': now
            }
            
            # Save to file
            await self._save_profiles()
            
            # Save to database
            await db_manager.create_voice_profile(
                user_id=user_id,
                username=username,
                language=language,
                accent=accent,
                gender=gender
            )
            
            logger.info(f"Created voice profile for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            return False
            
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a voice profile by user ID"""
        # Check in-memory cache
        if user_id in self.profiles:
            return {
                'user_id': user_id,
                **self.profiles[user_id]
            }
            
        # Try database
        try:
            db_profile = await db_manager.get_voice_profile(user_id)
            
            if db_profile:
                # Cache the profile
                self.profiles[user_id] = {
                    'username': db_profile['username'],
                    'language': db_profile['language'],
                    'accent': db_profile['accent'],
                    'gender': db_profile['gender'],
                    'created_at': db_profile['created_at'],
                    'updated_at': db_profile['updated_at']
                }
                
                return {
                    'user_id': user_id,
                    **self.profiles[user_id]
                }
        except Exception as e:
            logger.error(f"Error getting voice profile from database: {e}")
            
        return None
        
    async def get_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a voice profile by username"""
        # Check in-memory cache
        for user_id, profile in self.profiles.items():
            if profile['username'].lower() == username.lower():
                return {
                    'user_id': user_id,
                    **profile
                }
                
        # Try database
        try:
            db_profile = await db_manager.get_voice_profile_by_username(username)
            
            if db_profile:
                # Cache the profile
                user_id = db_profile['user_id']
                self.profiles[user_id] = {
                    'username': db_profile['username'],
                    'language': db_profile['language'],
                    'accent': db_profile['accent'],
                    'gender': db_profile['gender'],
                    'created_at': db_profile['created_at'],
                    'updated_at': db_profile['updated_at']
                }
                
                return {
                    'user_id': user_id,
                    **self.profiles[user_id]
                }
        except Exception as e:
            logger.error(f"Error getting voice profile from database: {e}")
            
        return None
        
    async def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all voice profiles"""
        result = {}
        
        # Add all in-memory profiles
        for user_id, profile in self.profiles.items():
            result[user_id] = {
                'user_id': user_id,
                **profile
            }
            
        return result
        
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update a voice profile"""
        # Check if profile exists
        existing = await self.get_profile(user_id)
        if not existing:
            return False
            
        try:
            now = datetime.now().isoformat()
            
            # Update profile
            updated_profile = {
                **self.profiles[user_id],
                **profile_data,
                'updated_at': now
            }
            
            self.profiles[user_id] = updated_profile
            
            # Save to file
            await self._save_profiles()
            
            # Update database
            await db_manager.update_voice_profile(user_id, {
                'language': updated_profile['language'],
                'accent': updated_profile['accent'],
                'gender': updated_profile['gender']
            })
            
            logger.info(f"Updated voice profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating voice profile: {e}")
            return False
            
    async def delete_profile(self, user_id: str) -> bool:
        """Delete a voice profile"""
        if user_id not in self.profiles:
            return False
            
        try:
            # Remove from in-memory cache
            del self.profiles[user_id]
            
            # Save to file
            await self._save_profiles()
            
            # Delete from database
            await db_manager.delete_voice_profile(user_id)
            
            logger.info(f"Deleted voice profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting voice profile: {e}")
            return False
            
    def get_language_options(self) -> List[Dict[str, str]]:
        """Get available language options"""
        return [
            {"value": "en-US", "label": "English (US)"},
            {"value": "en-GB", "label": "English (UK)"},
            {"value": "fr-FR", "label": "French"},
            {"value": "de-DE", "label": "German"},
            {"value": "es-ES", "label": "Spanish"},
            {"value": "it-IT", "label": "Italian"},
            {"value": "ja-JP", "label": "Japanese"}
        ]
        
    def get_accent_options(self) -> List[Dict[str, str]]:
        """Get available accent options"""
        return [
            {"value": "neutral", "label": "Neutral"},
            {"value": "british", "label": "British"},
            {"value": "american", "label": "American"},
            {"value": "australian", "label": "Australian"},
            {"value": "indian", "label": "Indian"},
            {"value": "scottish", "label": "Scottish"},
            {"value": "irish", "label": "Irish"}
        ]

# Create singleton instance
voice_profile_manager = VoiceProfileManager()