"""
Bishop Bot - Audio Initialization
Last updated: 2025-05-31 21:51:50 UTC by Bioku87

This script creates sample audio files for testing.
"""
import os
import wave
import struct
import math
import logging
import shutil
from pathlib import Path

logger = logging.getLogger('bishop_bot.init_audio')

def create_sine_wave(filename, freq=440, duration=1.0, volume=0.5, sample_rate=44100):
    """Create a sine wave audio file"""
    # Create directory if needed
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Generate audio data
    audio = []
    num_samples = int(duration * sample_rate)
    for i in range(num_samples):
        sample = volume * math.sin(2 * math.pi * freq * i / sample_rate)
        audio.append(int(sample * 32767))  # Convert to 16-bit
    
    # Write to WAV file
    with wave.open(filename, 'w') as wav_file:
        # Setup wav file
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write audio data
        for sample in audio:
            wav_file.writeframes(struct.pack('h', sample))
    
    logger.info(f"Created sine wave audio file: {filename}")

def init_sample_audio_files():
    """Create sample audio files for each category"""
    categories = ["Default", "Combat", "Ambience"]
    sounds = {
        "Default": [
            {"name": "beep", "freq": 440, "duration": 0.5},
            {"name": "welcome", "freq": 523, "duration": 1.0},
            {"name": "notification", "freq": 880, "duration": 0.3}
        ],
        "Combat": [
            {"name": "sword_slash", "freq": 220, "duration": 0.2},
            {"name": "bow_shot", "freq": 330, "duration": 0.15},
            {"name": "explosion", "freq": 110, "duration": 2.0}
        ],
        "Ambience": [
            {"name": "rain", "freq": 100, "duration": 5.0, "volume": 0.3},
            {"name": "wind", "freq": 80, "duration": 5.0, "volume": 0.3},
            {"name": "tavern", "freq": 160, "duration": 5.0, "volume": 0.3}
        ]
    }
    
    # Create each category directory and sample sounds
    for category in categories:
        category_dir = f"data/audio/soundboard/{category}"
        os.makedirs(category_dir, exist_ok=True)
        
        # Create each sound in the category
        for sound in sounds.get(category, []):
            filename = f"{category_dir}/{sound['name']}.wav"
            
            # Skip if file already exists
            if os.path.exists(filename):
                logger.info(f"Sound file already exists: {filename}")
                continue
                
            # Generate sound
            create_sine_wave(
                filename,
                freq=sound.get("freq", 440),
                duration=sound.get("duration", 1.0),
                volume=sound.get("volume", 0.5)
            )
    
    logger.info("Created all sample audio files")

def init_whisper_module():
    """Set up the whisper model if needed"""
    try:
        import whisper
        logger.info("Checking for Whisper model...")
        
        # Check if the model is already downloaded
        # Models are saved to ~/.cache/whisper by default
        home_dir = os.path.expanduser("~")
        whisper_cache_dir = os.path.join(home_dir, ".cache", "whisper")
        
        if os.path.exists(whisper_cache_dir):
            # Check if base model exists
            base_model_dir = os.path.join(whisper_cache_dir, "base.en.pt")
            if os.path.exists(base_model_dir):
                logger.info("Whisper base.en model already downloaded")
                return
        
        # Try to download the model
        logger.info("Downloading Whisper base model...")
        whisper.load_model("base.en")
        logger.info("Whisper model downloaded successfully")
    except ImportError:
        logger.warning("Whisper not installed. Voice transcription will be limited.")
    except Exception as e:
        logger.error(f"Error setting up Whisper: {e}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create sample audio files
    init_sample_audio_files()
    
    # Try to initialize whisper
    init_whisper_module()