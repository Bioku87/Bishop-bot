"""
Bishop Bot - Database Manager
Last updated: 2025-06-01 06:15:40 UTC by Bioku87
"""
import os
import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger('bishop_bot.database')

class DatabaseManager:
    """Manages database operations for Bishop Bot"""
    
    def __init__(self, db_path: str = None):
        """Initialize the database manager"""
        # Set default path if not provided
        if db_path is None:
            db_path = "data/database/bishop.db"
        
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_db()
        
        logger.info(f"Database manager initialized with database at: {db_path}")
    
    def _initialize_db(self):
        """Initialize the database schema"""
        try:
            # Connect to database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_data (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                settings TEXT,
                updated_at TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                session_id TEXT,
                file_path TEXT,
                created_at TIMESTAMP,
                metadata TEXT
            )
            ''')
            
            # Commit changes and close
            conn.commit()
            conn.close()
            
            logger.info("Database schema initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _get_connection(self):
        """Get a connection to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def get_value(self, key: str) -> Optional[str]:
        """Get a value from the bot_data table"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_data WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result['value']
            return None
        except Exception as e:
            logger.error(f"Error getting value for key '{key}': {e}")
            return None
    
    def set_value(self, key: str, value: str) -> bool:
        """Set a value in the bot_data table"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO bot_data (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error setting value for key '{key}': {e}")
            return False
    
    def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get settings for a guild"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT settings FROM guild_settings WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result['settings'])
            return {}
        except Exception as e:
            logger.error(f"Error getting settings for guild {guild_id}: {e}")
            return {}
    
    def save_guild_settings(self, guild_id: int, settings: Dict[str, Any]) -> bool:
        """Save settings for a guild"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, settings, updated_at) VALUES (?, ?, ?)",
                (guild_id, json.dumps(settings), datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving settings for guild {guild_id}: {e}")
            return False
    
    def save_transcript_metadata(self, guild_id: int, session_id: str, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Save metadata about a transcript"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transcripts 
                (guild_id, session_id, file_path, created_at, metadata) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (guild_id, session_id, file_path, datetime.now().isoformat(), json.dumps(metadata))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving transcript metadata for guild {guild_id}, session {session_id}: {e}")
            return False
    
    def get_transcripts(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get list of transcripts for a guild"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM transcripts WHERE guild_id = ? ORDER BY created_at DESC",
                (guild_id,)
            )
            results = cursor.fetchall()
            conn.close()
            
            transcripts = []
            for row in results:
                transcript = dict(row)
                # Parse JSON metadata
                if transcript.get('metadata'):
                    transcript['metadata'] = json.loads(transcript['metadata'])
                transcripts.append(transcript)
                
            return transcripts
        except Exception as e:
            logger.error(f"Error getting transcripts for guild {guild_id}: {e}")
            return []
    
    def close(self):
        """Close any open connections"""
        # No persistent connections to close in this implementation
        pass