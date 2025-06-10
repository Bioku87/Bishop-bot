"""
Bishop Bot - Audio Manager (Simplified)
Last updated: 2025-05-31 23:13:05 UTC by Bioku87
"""
import os
import logging
import discord
import shutil
from typing import Dict, List, Any, Optional

logger = logging.getLogger('bishop_bot.audio')

class AudioTrack:
    """Represents an audio track for the soundboard"""
    
    def __init__(self, name, category, file_path, **kwargs):
        self.name = name
        self.category = category
        self.file_path = file_path
        self.tags = kwargs.get('tags', [category.lower()])
        self.duration = kwargs.get('duration', 0.0)
        

class AudioManager:
    """Manages audio playback and soundboard functionality"""
    
    def __init__(self, bot):
        """Initialize the audio manager"""
        self.bot = bot
        self.voice_clients = {}  # guild_id -> voice_client
        self.now_playing = {}  # guild_id -> currently playing track
        
        # Scan for audio files
        self.sound_library = self._scan_audio_files()
        
        logger.info("Audio manager initialized")
    
    def _scan_audio_files(self):
        """Scan for audio files in soundboard directories"""
        library = {}
        
        try:
            # Scan standard categories
            categories = ["Default", "Combat", "Ambience"]
            for category in categories:
                library[category] = []
                
                category_dir = f"data/audio/soundboard/{category}"
                os.makedirs(category_dir, exist_ok=True)
                
                for file in os.listdir(category_dir):
                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                        file_path = os.path.join(category_dir, file)
                        name = os.path.splitext(file)[0]
                        
                        track = AudioTrack(
                            name=name,
                            category=category,
                            file_path=file_path,
                            tags=[category.lower()]
                        )
                        
                        library[category].append(track)
            
            # Log found sounds
            total_sounds = sum(len(sounds) for sounds in library.values())
            logger.info(f"Found {total_sounds} sounds across {len(library)} categories")
            
            return library
        except Exception as e:
            logger.error(f"Error scanning audio files: {e}")
            return {"Default": [], "Combat": [], "Ambience": []}
    
    async def join_voice_channel(self, channel):
        """Join a voice channel"""
        if not isinstance(channel, discord.VoiceChannel):
            logger.error(f"Invalid channel type: {type(channel).__name__}")
            return False
        
        guild_id = channel.guild.id
        
        # If already connected to this guild, disconnect first
        if guild_id in self.voice_clients:
            await self.disconnect_from_guild(guild_id)
        
        try:
            # Connect to the voice channel
            voice_client = await channel.connect()
            self.voice_clients[guild_id] = voice_client
            
            logger.info(f"Audio manager joined voice channel: {channel.name} in {channel.guild.name}")
            return True
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return False
    
    async def disconnect_from_guild(self, guild_id):
        """Disconnect from a guild's voice channel"""
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            return
        
        try:
            # Stop playing if necessary
            if voice_client.is_playing():
                voice_client.stop()
            
            # Disconnect
            await voice_client.disconnect()
            
            # Update tracking
            del self.voice_clients[guild_id]
            self.now_playing.pop(guild_id, None)
            
            logger.info(f"Audio manager disconnected from voice in guild {guild_id}")
        except Exception as e:
            logger.error(f"Error disconnecting from voice: {e}")
    
    async def play_sound(self, guild_id, sound_name, category="Default"):
        """Play a sound by name and category"""
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            logger.error(f"Not connected to voice in guild {guild_id}")
            return False
        
        try:
            # Find sound in library
            track = None
            for sound in self.sound_library.get(category, []):
                if sound.name.lower() == sound_name.lower():
                    track = sound
                    break
            
            if not track:
                logger.warning(f"Sound {sound_name} in category {category} not found")
                return False
            
            # Create audio source
            audio_source = discord.FFmpegPCMAudio(track.file_path)
            
            # Apply volume
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
            
            # Stop current playback
            if voice_client.is_playing():
                voice_client.stop()
            
            # Play the sound
            voice_client.play(audio_source)
            
            # Update tracking
            self.now_playing[guild_id] = track
            
            logger.info(f"Playing sound {sound_name} in guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error playing sound: {e}")
            return False
    
    def stop_playback(self, guild_id):
        """Stop audio playback in a guild"""
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client:
            return False
        
        try:
            if voice_client.is_playing():
                voice_client.stop()
                self.now_playing.pop(guild_id, None)
                logger.info(f"Stopped playback in guild {guild_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            return False
    
    def get_sounds_in_category(self, category):
        """Get all sounds in a category"""
        return self.sound_library.get(category, [])
    
    def get_all_sounds(self):
        """Get all available sounds"""
        all_sounds = []
        for sounds in self.sound_library.values():
            all_sounds.extend(sounds)
        return all_sounds
    
    def add_custom_sound(self, guild_id, name, file_path, category="Default"):
        """Add a custom sound to the soundboard"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Sound file not found: {file_path}")
                return False
            
            # Ensure category directory exists
            category_dir = f"data/audio/soundboard/{category}"
            os.makedirs(category_dir, exist_ok=True)
            
            # Copy file to sound directory
            dest_path = f"{category_dir}/{name}{os.path.splitext(file_path)[1]}"
            shutil.copy2(file_path, dest_path)
            
            # Create track
            track = AudioTrack(
                name=name,
                category=category,
                file_path=dest_path,
                tags=[category.lower()]
            )
            
            # Add to library
            if category not in self.sound_library:
                self.sound_library[category] = []
            self.sound_library[category].append(track)
            
            logger.info(f"Added custom sound {name} to category {category}")
            return True
        except Exception as e:
            logger.error(f"Error adding custom sound: {e}")
            return False
    
    def is_connected(self, guild_id):
        """Check if connected to a voice channel in the guild"""
        voice_client = self.voice_clients.get(guild_id)
        return voice_client is not None and voice_client.is_connected()