"""
Bishop Bot - Voice Processing System
Last updated: 2025-05-31 15:56:17 UTC by Bioku87

This module handles the voice processing system for the bot.
"""
import asyncio
import logging
import discord
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger('bishop_bot.voice')

class VoiceSystem:
    """Main voice processing system for Bishop Bot"""
    
    def __init__(self):
        """Initialize the voice system"""
        self.active_voice_connections = {}
        self.processing_enabled = {}
        self.listeners = {}
        self.callback = None
        
        # Session state
        self.current_session = None
        self.session_name = None
        
        # Import components lazily to avoid circular imports
        self._voice_processor = None
        self._speech_processor = None
        self._music_player = None
        self._voice_profile_manager = None
        
        logger.info("Voice system initialized")
        
    @property
    def voice_processor(self):
        if self._voice_processor is None:
            # Import here to avoid circular imports
            from .processor import VoiceProcessor
            self._voice_processor = VoiceProcessor()
        return self._voice_processor
        
    @property
    def speech_processor(self):
        if self._speech_processor is None:
            # Import here to avoid circular imports
            from .speech_processor import speech_processor
            self._speech_processor = speech_processor
        return self._speech_processor
        
    @property
    def music_player(self):
        if self._music_player is None:
            # Import here to avoid circular imports
            from .music_player import music_player
            self._music_player = music_player
        return self._music_player
        
    @property
    def voice_profile_manager(self):
        if self._voice_profile_manager is None:
            # Import here to avoid circular imports
            from .profiles import voice_profile_manager
            self._voice_profile_manager = voice_profile_manager
        return self._voice_profile_manager
        
    async def initialize(self):
        """Initialize the voice system components"""
        await self.voice_profile_manager.initialize()
        logger.info("Voice system components initialized")
        
    async def connect_to_voice(self, ctx, channel=None):
        """Connect to a voice channel"""
        if not channel and ctx.author.voice:
            channel = ctx.author.voice.channel
            
        if not channel:
            return False, "You must be in a voice channel or specify a channel."
            
        guild_id = ctx.guild.id
        
        # Check if already connected
        if guild_id in self.active_voice_connections and self.active_voice_connections[guild_id].is_connected():
            await self.active_voice_connections[guild_id].move_to(channel)
            return True, f"Moved to {channel.name}"
            
        # Connect to voice channel
        try:
            voice_client = await channel.connect()
            self.active_voice_connections[guild_id] = voice_client
            self.processing_enabled[guild_id] = False
            
            logger.info(f"Connected to voice channel: {channel.name} in {ctx.guild.name}")
            return True, f"Connected to {channel.name}"
        except discord.ClientException as e:
            logger.error(f"Error connecting to voice: {e}")
            return False, f"Error connecting to voice: {e}"
    
    async def disconnect_from_voice(self, guild_id):
        """Disconnect from a voice channel"""
        if guild_id in self.active_voice_connections:
            voice_client = self.active_voice_connections[guild_id]
            
            if voice_client.is_connected():
                # Stop processing
                self.processing_enabled[guild_id] = False
                
                # Disconnect
                await voice_client.disconnect()
                logger.info(f"Disconnected from voice in guild {guild_id}")
                
                # Clean up
                del self.active_voice_connections[guild_id]
                if guild_id in self.processing_enabled:
                    del self.processing_enabled[guild_id]
                if guild_id in self.listeners:
                    del self.listeners[guild_id]
                    
                return True, "Disconnected from voice channel."
                
        return False, "Not connected to any voice channel."
    
    async def start_voice_processing(self, guild_id, callback=None):
        """Start processing voice in a guild"""
        if guild_id not in self.active_voice_connections:
            return False, "Not connected to a voice channel."
            
        voice_client = self.active_voice_connections[guild_id]
        
        if not voice_client.is_connected():
            return False, "Voice client is not connected."
            
        # Set up callback
        if callback:
            self.callback = callback
            
        # Enable processing
        self.processing_enabled[guild_id] = True
        
        # Start listening
        self.listeners[guild_id] = self.voice_processor.start_listening(
            voice_client, 
            self.on_audio_received
        )
        
        # Start a session if not already started
        if not self.current_session:
            name = self.session_name or f"Session_{guild_id}"
            self.current_session = self.speech_processor.start_session(name)
            
        logger.info(f"Started voice processing in guild {guild_id}")
        return True, "Started voice processing."
    
    async def stop_voice_processing(self, guild_id):
        """Stop processing voice in a guild"""
        if guild_id not in self.processing_enabled or not self.processing_enabled[guild_id]:
            return False, "Voice processing is not active."
            
        # Disable processing
        self.processing_enabled[guild_id] = False
        
        # Stop listening
        if guild_id in self.listeners:
            self.voice_processor.stop_listening(self.listeners[guild_id])
            del self.listeners[guild_id]
            
        logger.info(f"Stopped voice processing in guild {guild_id}")
        return True, "Stopped voice processing."
    
    async def on_audio_received(self, user_id, audio_data, username=None):
        """Process received audio data"""
        if not audio_data:
            return
            
        # Process audio with speech recognition
        result = await self.speech_processor.process_audio(audio_data, user_id, username)
        
        # If we got a result and have a callback, call it
        if result and self.callback:
            await self.callback(result)
            
        return result
    
    async def start_session(self, name=None):
        """Start a new transcription session"""
        # End any current session
        if self.current_session:
            await self.end_session()
            
        # Start new session
        self.session_name = name
        self.current_session = self.speech_processor.start_session(name)
        
        logger.info(f"Started voice session: {name}")
        return True, f"Started voice session: {name}"
    
    async def end_session(self):
        """End the current transcription session"""
        if not self.current_session:
            return False, "No active session to end."
            
        # Stop session
        session_result = self.speech_processor.stop_session()
        
        # Reset state
        self.current_session = None
        self.session_name = None
        
        if session_result:
            # Export session
            filepath = self.speech_processor.export_session(session_result)
            
            logger.info(f"Ended voice session, saved to {filepath}")
            return True, f"Session ended and saved to {filepath}"
        
        return True, "Session ended."
    
    def get_session_stats(self):
        """Get stats for the current session"""
        if not self.current_session:
            return None
            
        return self.speech_processor.get_session_stats()
    
    async def play_audio(self, ctx, url=None, file=None):
        """Play audio in a voice channel"""
        # Delegate to music player
        if url:
            success, message = await self.music_player.play(ctx, url)
        elif file:
            # TODO: Implement file playback
            success, message = False, "File playback not implemented yet"
        else:
            success, message = False, "No URL or file specified"
            
        return success, message
    
    async def stop_audio(self, ctx):
        """Stop audio playback"""
        return self.music_player.stop(ctx)
    
    async def pause_audio(self, ctx):
        """Pause audio playback"""
        return self.music_player.pause(ctx)
    
    async def resume_audio(self, ctx):
        """Resume audio playback"""
        return self.music_player.resume(ctx)
    
    async def skip_audio(self, ctx):
        """Skip current audio track"""
        return self.music_player.skip(ctx)
    
    async def set_volume(self, ctx, volume):
        """Set audio volume"""
        return self.music_player.set_volume(ctx, volume)
    
    async def get_queue(self, ctx):
        """Get the current audio queue"""
        return self.music_player.get_queue(ctx)
        
    async def cleanup(self):
        """Clean up voice resources"""
        # Stop all voice processing
        for guild_id in list(self.processing_enabled.keys()):
            await self.stop_voice_processing(guild_id)
            
        # Disconnect from all voice channels
        for guild_id in list(self.active_voice_connections.keys()):
            await self.disconnect_from_voice(guild_id)
            
        # Clean up music player
        self.music_player.cleanup()
        
        # End any active session
        if self.current_session:
            await self.end_session()

# Create singleton instance
voice_system = VoiceSystem()