"""
Bishop Bot - Project Structure Initialization
Last updated: 2025-05-31 18:16:31 UTC by Bioku87
"""
import os
import logging
import json
import shutil

logger = logging.getLogger('bishop_bot.init')

def create_directory_structure():
    """Create comprehensive directory structure for Bishop Bot"""
    directories = [
        # Core directories
        "logs",
        "data",
        "assets",
        "config",
        
        # Bot modules
        "src/bot",
        "src/bot/commands",
        "src/bot/cogs",
        "src/bot/events",
        
        # Voice features
        "src/voice",
        "src/voice/recognition",
        "src/voice/transcription",
        "src/voice/generation",
        
        # Character management
        "src/characters",
        "src/characters/sheets",
        "src/characters/templates",
        
        # Audio system
        "src/audio",
        "src/audio/playback",
        "src/audio/effects",
        
        # Game mechanics
        "src/game",
        "src/game/dice",
        "src/game/rules",
        
        # UI components
        "src/ui",
        "src/ui/windows",
        "src/ui/widgets",
        
        # Data storage
        "data/database",
        "data/characters",
        "data/sessions",
        "data/audio/soundboard/Default",
        "data/audio/soundboard/Combat",
        "data/audio/soundboard/Ambience",
        "data/voice/profiles",
        "data/voice/samples",
        "data/voice/transcripts",
        "data/exports",
        "data/imports",
        "data/temp",
        
        # Assets
        "assets/images",
        "assets/icons",
        "assets/fonts",
        
        # Config files
        "config/templates",
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            
    # Create default config files
    create_default_config_files()
    
    return True

def create_default_config_files():
    """Create default configuration files"""
    # Main config
    main_config = {
        "version": "1.0.0",
        "name": "Bishop Bot",
        "description": "Advanced Discord bot for tabletop RPG sessions",
        "features": {
            "voice_recognition": True,
            "character_management": True,
            "audio_playback": True,
            "dice_rolling": True,
            "session_management": True
        },
        "settings": {
            "default_command_prefix": "/",
            "default_volume": 0.5,
            "transcription_enabled": True,
            "auto_backup": True,
            "backup_interval_hours": 24
        }
    }
    
    # Voice recognition config
    voice_config = {
        "engine": "whisper",
        "model": "medium",
        "language": "en",
        "sample_rate": 16000,
        "chunk_size": 1024,
        "silence_threshold": 500,
        "silence_duration": 1.0,
        "keyword_activation": True,
        "keywords": ["bishop", "hey bishop", "computer"]
    }
    
    # Audio config
    audio_config = {
        "default_volume": 0.5,
        "fade_in_ms": 100,
        "fade_out_ms": 100,
        "audio_device": "default",
        "channels": 2,
        "sample_rate": 44100,
        "bit_depth": 16,
        "sound_packs": ["Default", "Combat", "Ambience"]
    }
    
    # Save config files
    try:
        with open("config/main_config.json", "w") as f:
            json.dump(main_config, f, indent=4)
            
        with open("config/voice_config.json", "w") as f:
            json.dump(voice_config, f, indent=4)
            
        with open("config/audio_config.json", "w") as f:
            json.dump(audio_config, f, indent=4)
            
        logger.info("Created default configuration files")
    except Exception as e:
        logger.error(f"Error creating config files: {e}")

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create project structure
    create_directory_structure()
    print("Project structure initialized successfully!")