"""
Bishop Bot - Database Initialization
Last updated: 2025-05-31 21:20:10 UTC by Bioku87

This script initializes the database with default data for testing.
"""
import os
import json
import logging
from .manager import DatabaseManager

logger = logging.getLogger('bishop_bot.database.init')

def initialize_database_with_test_data():
    """Initialize the database with test data"""
    logger.info("Initializing database with test data")
    
    # Create database manager instance
    db = DatabaseManager()
    
    # Add test guild settings
    add_test_guild_settings(db)
    
    # Add test audio tracks
    add_test_audio_tracks(db)
    
    # Add test character data
    add_test_character_data(db)
    
    logger.info("Database initialized with test data")

def add_test_guild_settings(db):
    """Add test guild settings to the database"""
    try:
        # Check if we already have guild settings
        if db.fetchone("SELECT COUNT(*) as count FROM guild_settings", ())['count'] > 0:
            logger.info("Guild settings already exist, skipping")
            return
            
        # Add test guild settings
        test_guild_id = '123456789012345678'
        settings = {
            'prefix': '/',
            'welcome_channel': '123456789012345679',
            'admin_role': '123456789012345680',
            'voice_recognition_enabled': True,
            'default_volume': 0.5
        }
        
        db.insert('guild_settings', {
            'guild_id': test_guild_id,
            'settings': json.dumps(settings)
        })
        
        logger.info("Added test guild settings")
    except Exception as e:
        logger.error(f"Error adding test guild settings: {e}")

def add_test_audio_tracks(db):
    """Add test audio tracks to the database"""
    try:
        # Check if we already have audio tracks
        if db.fetchone("SELECT COUNT(*) as count FROM audio_tracks", ())['count'] > 0:
            logger.info("Audio tracks already exist, skipping")
            return
            
        # Create audio directories if they don't exist
        for category in ['Default', 'Combat', 'Ambience']:
            os.makedirs(f"data/audio/soundboard/{category}", exist_ok=True)
            
        # Add test audio tracks
        test_tracks = [
            {
                'guild_id': 'global',
                'category': 'Default',
                'name': 'Welcome',
                'file_path': 'data/audio/soundboard/Default/welcome.mp3',
                'duration': 2.5,
                'tags': json.dumps(['greeting', 'welcome']),
                'created_by': 'system'
            },
            {
                'guild_id': 'global',
                'category': 'Combat',
                'name': 'Sword Clash',
                'file_path': 'data/audio/soundboard/Combat/sword_clash.mp3',
                'duration': 1.2,
                'tags': json.dumps(['combat', 'sword']),
                'created_by': 'system'
            },
            {
                'guild_id': 'global',
                'category': 'Ambience',
                'name': 'Tavern',
                'file_path': 'data/audio/soundboard/Ambience/tavern.mp3',
                'duration': 60.0,
                'tags': json.dumps(['ambience', 'tavern']),
                'created_by': 'system'
            }
        ]
        
        for track in test_tracks:
            # Create empty audio file if it doesn't exist
            if not os.path.exists(track['file_path']):
                with open(track['file_path'], 'wb') as f:
                    # Create an empty MP3 file
                    f.write(b'')
                    
            db.insert('audio_tracks', track)
            
        logger.info("Added test audio tracks")
    except Exception as e:
        logger.error(f"Error adding test audio tracks: {e}")

def add_test_character_data(db):
    """Add test character data to the database"""
    try:
        # Check if we already have characters
        if db.fetchone("SELECT COUNT(*) as count FROM characters", ())['count'] > 0:
            logger.info("Characters already exist, skipping")
            return
            
        # Add test characters
        test_user_id = '111222333444555666'
        test_guild_id = '123456789012345678'
        
        test_characters = [
            {
                'name': 'Aragorn',
                'player_id': test_user_id,
                'guild_id': test_guild_id,
                'character_class': 'Ranger',
                'level': 5,
                'race': 'Human',
                'background': 'Outlander',
                'alignment': 'Lawful Good',
                'experience': 5000,
                'attributes': json.dumps({
                    'strength': 16,
                    'dexterity': 14,
                    'constitution': 15,
                    'intelligence': 12,
                    'wisdom': 14,
                    'charisma': 13
                }),
                'skills': json.dumps({
                    'acrobatics': {'ability': 'dexterity', 'proficient': False},
                    'animal handling': {'ability': 'wisdom', 'proficient': True},
                    'arcana': {'ability': 'intelligence', 'proficient': False},
                    'athletics': {'ability': 'strength', 'proficient': True},
                    'survival': {'ability': 'wisdom', 'proficient': True}
                }),
                'inventory': json.dumps({
                    'gold': 50,
                    'items': [
                        {'name': 'Longsword', 'quantity': 1, 'description': 'A well-crafted blade'},
                        {'name': 'Bow', 'quantity': 1, 'description': 'A ranger\'s bow'},
                        {'name': 'Arrow', 'quantity': 20, 'description': 'Standard arrows'}
                    ]
                }),
                'notes': 'Hero of Gondor, heir to the throne'
            },
            {
                'name': 'Gandalf',
                'player_id': test_user_id,
                'guild_id': test_guild_id,
                'character_class': 'Wizard',
                'level': 10,
                'race': 'Human',
                'background': 'Sage',
                'alignment': 'Neutral Good',
                'experience': 24000,
                'attributes': json.dumps({
                    'strength': 10,
                    'dexterity': 12,
                    'constitution': 13,
                    'intelligence': 18,
                    'wisdom': 16,
                    'charisma': 15
                }),
                'skills': json.dumps({
                    'acrobatics': {'ability': 'dexterity', 'proficient': False},
                    'arcana': {'ability': 'intelligence', 'proficient': True},
                    'history': {'ability': 'intelligence', 'proficient': True},
                    'nature': {'ability': 'intelligence', 'proficient': True},
                    'religion': {'ability': 'intelligence', 'proficient': True}
                }),
                'inventory': json.dumps({
                    'gold': 120,
                    'items': [
                        {'name': 'Staff', 'quantity': 1, 'description': 'A magical staff'},
                        {'name': 'Spellbook', 'quantity': 1, 'description': 'Contains many spells'},
                        {'name': 'Pipe', 'quantity': 1, 'description': 'For smoking pipe-weed'}
                    ]
                }),
                'notes': 'The Grey Wizard, a member of the Istari'
            }
        ]
        
        for character in test_characters:
            db.insert('characters', character)
            
        logger.info("Added test characters")
    except Exception as e:
        logger.error(f"Error adding test characters: {e}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the database with test data
    initialize_database_with_test_data()