"""
Bishop Bot - Voice Processor
Last updated: 2025-05-31 15:56:17 UTC by Bioku87

This module processes voice audio for transcription.
"""
import io
import time
import array
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List

import discord

logger = logging.getLogger('bishop_bot.voice.processor')

class VoiceProcessor:
    """Processes voice audio data from Discord voice channels"""
    
    def __init__(self):
        """Initialize the voice processor"""
        self.listeners = {}
        self.listener_id = 0
        self.frame_size = 1920  # PCM frame size (20ms of 48kHz audio)
        self.buffer_limit = 50  # Max number of frames to buffer per user
        
        logger.info("Voice processor initialized")
        
    def start_listening(self, voice_client, callback):
        """Start listening to a voice client"""
        if not voice_client or not voice_client.is_connected():
            logger.error("Cannot listen: voice client not connected")
            return None
            
        # Generate listener ID
        self.listener_id += 1
        listener_id = self.listener_id
        
        # Initialize listener data
        self.listeners[listener_id] = {
            "voice_client": voice_client,
            "callback": callback,
            "user_buffers": {},
            "active": True
        }
        
        # Set up audio reception
        voice_client.listen(self._audio_receiver_factory(listener_id))
        
        logger.info(f"Started listening (ID: {listener_id})")
        return listener_id
        
    def stop_listening(self, listener_id):
        """Stop listening to a voice client"""
        if listener_id not in self.listeners:
            logger.warning(f"Cannot stop non-existent listener: {listener_id}")
            return False
            
        listener = self.listeners[listener_id]
        
        # Mark as inactive
        listener["active"] = False
        
        # Stop listening
        voice_client = listener["voice_client"]
        if voice_client and voice_client.is_connected():
            voice_client.stop_listening()
            
        # Cleanup
        del self.listeners[listener_id]
        
        logger.info(f"Stopped listening (ID: {listener_id})")
        return True
        
    def _audio_receiver_factory(self, listener_id):
        """Create an audio receiver for the voice client"""
        
        async def audio_receiver(user, audio):
            await self._process_audio(listener_id, user, audio)
            
        return audio_receiver
        
    async def _process_audio(self, listener_id, user, audio):
        """Process received audio data"""
        if listener_id not in self.listeners or not self.listeners[listener_id]["active"]:
            return
            
        listener = self.listeners[listener_id]
        user_buffers = listener["user_buffers"]
        
        # Add audio to user buffer
        if user.id not in user_buffers:
            user_buffers[user.id] = {
                "buffer": [],
                "last_packet": time.time(),
                "username": user.name,
                "speaking": False
            }
            
        user_data = user_buffers[user.id]
        user_data["buffer"].append(audio)
        user_data["last_packet"] = time.time()
        
        # Check if buffer is full or user stopped speaking
        if len(user_data["buffer"]) >= self.buffer_limit:
            await self._process_user_buffer(listener_id, user.id)
            
        # Schedule check for silence
        asyncio.create_task(self._check_user_silence(listener_id, user.id))
            
    async def _process_user_buffer(self, listener_id, user_id):
        """Process the audio buffer for a user"""
        if listener_id not in self.listeners:
            return
            
        listener = self.listeners[listener_id]
        user_buffers = listener["user_buffers"]
        
        if user_id not in user_buffers:
            return
            
        user_data = user_buffers[user_id]
        
        # Skip if buffer is empty
        if not user_data["buffer"]:
            return
            
        # Combine audio data
        combined_audio = b"".join(user_data["buffer"])
        user_data["buffer"] = []
        
        # Process through callback
        if listener["callback"] and combined_audio:
            try:
                await listener["callback"](user_id, combined_audio, user_data["username"])
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")
                
    async def _check_user_silence(self, listener_id, user_id):
        """Check if user has been silent for a while and process buffer"""
        # Wait for potential silence
        await asyncio.sleep(0.5)  # 500ms silence threshold
        
        if listener_id not in self.listeners:
            return
            
        listener = self.listeners[listener_id]
        user_buffers = listener["user_buffers"]
        
        if user_id not in user_buffers:
            return
            
        user_data = user_buffers[user_id]
        
        # If it's been more than 0.5 seconds since the last packet and there's data in the buffer
        if (time.time() - user_data["last_packet"] >= 0.5 and 
            user_data["buffer"] and 
            user_data["speaking"]):
            
            # User stopped speaking, process the buffer
            user_data["speaking"] = False
            await self._process_user_buffer(listener_id, user_id)
        elif not user_data["speaking"] and user_data["buffer"]:
            # User started speaking
            user_data["speaking"] = True