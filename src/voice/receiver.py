"""
Bishop Bot - Voice Receiver
Last updated: 2025-05-31 05:18:51 UTC by Bioku87

This module handles receiving audio from Discord voice channels.
"""
import discord
import asyncio
import logging
import time
import struct
import io
from typing import Dict, List, Optional, Any, Callable

# Configure logger
logger = logging.getLogger("bishop_bot.voice.receiver")

class VoiceReceiver:
    """
    Handles receiving and processing audio from Discord voice channels
    Connects to voice channel and streams audio to processor
    """
    
    def __init__(self, voice_processor):
        """
        Initialize the voice receiver
        
        Args:
            voice_processor: The voice processor to send audio to
        """
        self.voice_processor = voice_processor
        self.active_receivers = {}  # guild_id -> receiver info
    
    async def start_receiving(self, voice_client):
        """
        Start receiving audio from a voice client
        
        Args:
            voice_client: Discord voice client
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not voice_client or not voice_client.is_connected():
            logger.error("Voice client not connected")
            return False
            
        guild_id = str(voice_client.guild.id)
        
        try:
            # Check if already receiving for this guild
            if guild_id in self.active_receivers:
                logger.info(f"Already receiving audio for guild {guild_id}")
                return True
                
            # Set up the receiver
            receiver = voice_client.receive_audio()
            sink = discord.sinks.WaveSink()
            
            # Start receiving
            voice_client.start_recording(sink,
                                       finished_callback=self._recording_finished, 
                                       on_audio_packet=self._on_audio_packet)
            
            # Store receiver info
            self.active_receivers[guild_id] = {
                "voice_client": voice_client,
                "sink": sink,
                "start_time": time.time()
            }
            
            logger.info(f"Started receiving audio for guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting voice receiver: {e}")
            return False
    
    async def stop_receiving(self, guild_id):
        """
        Stop receiving audio for a guild
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        guild_id = str(guild_id)
        
        try:
            # Check if receiving for this guild
            if guild_id not in self.active_receivers:
                logger.info(f"Not receiving audio for guild {guild_id}")
                return False
                
            # Stop recording
            receiver_info = self.active_receivers[guild_id]
            voice_client = receiver_info["voice_client"]
            
            if voice_client and voice_client.is_connected():
                voice_client.stop_recording()
            
            # Remove receiver info
            del self.active_receivers[guild_id]
            
            logger.info(f"Stopped receiving audio for guild {guild_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping voice receiver: {e}")
            # Try to remove receiver info anyway
            if guild_id in self.active_receivers:
                del self.active_receivers[guild_id]
            return False
    
    def stop_all_receivers(self):
        """
        Stop all active receivers
        
        Returns:
            int: Number of receivers stopped
        """
        try:
            count = len(self.active_receivers)
            
            for guild_id, receiver_info in list(self.active_receivers.items()):
                voice_client = receiver_info["voice_client"]
                
                if voice_client and voice_client.is_connected():
                    voice_client.stop_recording()
            
            # Clear all receivers
            self.active_receivers = {}
            
            logger.info(f"Stopped all receivers ({count})")
            return count
        except Exception as e:
            logger.error(f"Error stopping all receivers: {e}")
            self.active_receivers = {}
            return 0
    
    async def _recording_finished(self, sink, guild_id, *args):
        """
        Callback when recording is finished
        
        Args:
            sink: The audio sink
            guild_id: Discord guild ID
        """
        guild_id = str(guild_id)
        
        try:
            logger.info(f"Recording finished for guild {guild_id}")
            
            # Process the recorded audio if needed
            # This is typically for batch processing, not live transcription
            
            # Clean up
            if guild_id in self.active_receivers:
                del self.active_receivers[guild_id]
        except Exception as e:
            logger.error(f"Error in recording finished callback: {e}")