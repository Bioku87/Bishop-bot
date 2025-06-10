"""
Bishop Bot - Enhanced Voice Manager
Last updated: 2025-06-01 06:08:56 UTC by Bioku87
"""
import os
import logging
import asyncio
import json
import wave
import time
from typing import Dict, Any, Optional, List
import discord
from datetime import datetime

# Import whisper for transcription if available
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Voice transcription will be limited.")

logger = logging.getLogger('bishop_bot.voice')

class AudioReceiver(discord.AudioSink):
    """Receives and processes audio data from a Discord voice channel"""
    
    def __init__(self, *, filename=None, user_audio_map=None):
        self.filename = filename
        self.user_audio_map = user_audio_map or {}
        self.audio_data = {}
        self.wav_file = None
        
        if self.filename:
            self._setup_wav_file()
            
    def _setup_wav_file(self):
        """Set up the WAV file for recording"""
        try:
            directory = os.path.dirname(self.filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            self.wav_file = wave.open(self.filename, 'wb')
            self.wav_file.setnchannels(2)
            self.wav_file.setsampwidth(2)  # 16-bit audio
            self.wav_file.setframerate(48000)  # Discord audio rate
            logger.info(f"Set up recording to file: {self.filename}")
        except Exception as e:
            logger.error(f"Error setting up WAV file: {e}")
            self.wav_file = None
    
    def cleanup(self):
        """Clean up resources"""
        if self.wav_file:
            self.wav_file.close()
            self.wav_file = None
            
    def write(self, data, user):
        """Write audio data from a user"""
        # Store audio data by user
        if user.id not in self.audio_data:
            self.audio_data[user.id] = []
            
        self.audio_data[user.id].append((data.data, data.timestamp))
        
        # Keep user audio map updated
        self.user_audio_map[user.id] = {
            'name': user.name,
            'id': user.id,
            'display_name': user.display_name,
            'last_timestamp': data.timestamp
        }
        
        # Write to WAV file if available
        if self.wav_file:
            try:
                self.wav_file.writeframes(data.data)
            except Exception as e:
                logger.error(f"Error writing to WAV file: {e}")

class VoiceManager:
    """Manages voice connections, recording, and transcription"""
    
    def __init__(self, bot):
        """Initialize the voice manager"""
        logger.info("Initializing ultra simplified voice manager...")
        
        # Store the bot reference
        self.bot = bot
        
        # Initialize dictionaries for tracking with safe defaults
        self.voice_clients = {}
        self.audio_receivers = {}
        self.recording_sessions = {}
        self.user_audio_maps = {}
        self.transcription_model = None
        
        # Set up transcription if available
        self._setup_transcription()
        
        # Ensure required directories exist
        os.makedirs("data/voice/sessions", exist_ok=True)
        os.makedirs("data/voice/profiles", exist_ok=True)
        
        logger.info("Voice manager minimally initialized")
    
    def _setup_transcription(self):
        """Set up the transcription model"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available. Voice transcription will be disabled.")
            return
        
        try:
            # Use base model for English - small enough to work on most systems
            logger.info("Attempting to load Whisper model: base.en")
            self.transcription_model = whisper.load_model("base.en")
            logger.info("Whisper model 'base.en' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading transcription model: {e}")
            self.transcription_model = None
    
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
            
            # Initialize user audio map for this guild
            if guild_id not in self.user_audio_maps:
                self.user_audio_maps[guild_id] = {}
                
            logger.info(f"Joined voice channel: {channel.name} in {channel.guild.name}")
            return True
        except Exception as e:
            logger.error(f"Error joining voice channel: {e}")
            return False
    
    async def disconnect_from_guild(self, guild_id):
        """Disconnect from a guild's voice channel"""
        voice_client = self.voice_clients.get(guild_id)
        if voice_client:
            # Stop recording if active
            if guild_id in self.recording_sessions:
                await self.stop_recording(guild_id)
            
            # Disconnect
            try:
                await voice_client.disconnect()
                logger.info(f"Disconnected from voice in guild {guild_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from voice: {e}")
            
            # Remove from tracking
            self.voice_clients.pop(guild_id, None)
            
            # Clean up audio receiver if exists
            if guild_id in self.audio_receivers:
                try:
                    self.audio_receivers[guild_id].cleanup()
                except Exception:
                    pass
                self.audio_receivers.pop(guild_id, None)
                    
            return True
        return False
    
    async def start_recording(self, guild_id):
        """Start recording audio in a guild"""
        voice_client = self.voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_connected():
            logger.error(f"Not connected to voice in guild {guild_id}")
            return False
        
        # Check if already recording
        if guild_id in self.recording_sessions:
            logger.warning(f"Already recording in guild {guild_id}")
            return False
        
        try:
            # Generate session ID
            timestamp = int(time.time())
            session_id = f"session_{timestamp}"
            
            # Create directory for recording
            session_path = f"data/voice/sessions/guild_{guild_id}/{session_id}"
            os.makedirs(session_path, exist_ok=True)
            
            # Create filename for recording
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_path}/recording_{timestamp_str}.wav"
            
            # Create user audio map for this session
            user_audio_map = {}
            self.user_audio_maps[guild_id] = user_audio_map
            
            # Create audio receiver
            audio_receiver = AudioReceiver(filename=filename, user_audio_map=user_audio_map)
            self.audio_receivers[guild_id] = audio_receiver
            
            # Start listening
            voice_client.listen(audio_receiver)
            
            # Store recording info
            self.recording_sessions[guild_id] = {
                "start_time": time.time(),
                "filename": filename,
                "session_id": session_id,
                "session_path": session_path,
                "user_audio_map": user_audio_map
            }
            
            logger.info(f"Started recording in guild {guild_id}, session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
    
    async def stop_recording(self, guild_id):
        """Stop recording audio in a guild"""
        if guild_id not in self.recording_sessions:
            logger.warning(f"Not recording in guild {guild_id}")
            return False
        
        voice_client = self.voice_clients.get(guild_id)
        recording_info = self.recording_sessions[guild_id]
        audio_receiver = self.audio_receivers.get(guild_id)
        
        try:
            # Stop listening
            if voice_client and hasattr(voice_client, 'stop_listening'):
                voice_client.stop_listening()
            
            # Clean up audio receiver
            if audio_receiver:
                audio_receiver.cleanup()
                
            # Don't delete yet, just in case we need it for processing
            
            # Get recording info
            session_id = recording_info["session_id"]
            filename = recording_info["filename"]
            duration = time.time() - recording_info["start_time"]
            user_audio_map = recording_info.get("user_audio_map", {})
            
            # Save user map to file
            if filename and user_audio_map:
                user_map_file = filename.replace(".wav", "_users.json")
                try:
                    with open(user_map_file, "w") as f:
                        json.dump(user_audio_map, f, indent=4)
                except Exception as e:
                    logger.error(f"Error saving user map: {e}")
            
            # Process the recording (transcribe, etc.)
            if WHISPER_AVAILABLE and self.transcription_model:
                # Don't await, let it happen in the background
                asyncio.create_task(self._process_recording(guild_id, recording_info))
            
            # Remove from tracking
            self.recording_sessions.pop(guild_id, None)
            self.audio_receivers.pop(guild_id, None)
            
            logger.info(f"Stopped recording in guild {guild_id}. Duration: {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False
    
    async def _process_recording(self, guild_id, recording_info):
        """Process a recording (transcribe, etc.)"""
        try:
            filename = recording_info.get("filename")
            session_path = recording_info.get("session_path")
            user_audio_map = recording_info.get("user_audio_map", {})
            
            if not filename or not os.path.exists(filename):
                logger.error(f"Recording file not found: {filename}")
                return None
            
            # Transcribe the audio
            if not WHISPER_AVAILABLE or not self.transcription_model:
                logger.warning("Transcription skipped - Whisper not available")
                return None
                
            logger.info(f"Transcribing audio: {filename}")
            
            # Create transcript filename
            transcript_file = filename.replace(".wav", "_transcript.txt")
            
            # Transcribe using whisper
            try:
                result = self.transcription_model.transcribe(filename)
                
                # Format transcript with user info
                with open(transcript_file, "w", encoding="utf-8") as f:
                    f.write(f"Session Transcript - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Guild: {guild_id}\n")
                    f.write(f"Session: {recording_info.get('session_id', 'unknown')}\n")
                    f.write(f"Participants: {', '.join([info.get('name', 'Unknown') for info in user_audio_map.values()])}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Write main transcript
                    f.write(result["text"])
                    
                    # Add user information at the end
                    f.write("\n\n" + "="*50 + "\n")
                    f.write("Session Participants:\n")
                    for user_id, info in user_audio_map.items():
                        f.write(f"- {info.get('name', 'Unknown')} (ID: {user_id})\n")
                
                # Create timestamped transcript if segments are available
                if "segments" in result:
                    timestamped_file = filename.replace(".wav", "_timestamped.txt")
                    
                    with open(timestamped_file, "w", encoding="utf-8") as f:
                        f.write(f"Timestamped Transcript - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Guild: {guild_id}\n")
                        f.write(f"Session: {recording_info.get('session_id', 'unknown')}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for segment in result["segments"]:
                            start = segment["start"]
                            end = segment["end"]
                            text = segment["text"]
                            
                            # Format time as MM:SS
                            start_time = f"{int(start//60):02d}:{int(start%60):02d}"
                            end_time = f"{int(end//60):02d}:{int(end%60):02d}"
                            
                            f.write(f"[{start_time} - {end_time}] {text}\n")
                            
                logger.info(f"Transcription saved to: {transcript_file}")
                
                # Save to database if available
                if hasattr(self.bot, 'db') and self.bot.db:
                    try:
                        metadata = {
                            "session_id": recording_info.get('session_id'),
                            "duration": time.time() - recording_info.get('start_time', 0),
                            "participants": user_audio_map,
                            "has_timestamped": "segments" in result
                        }
                        self.bot.db.save_transcript_metadata(
                            guild_id, 
                            recording_info.get('session_id'),
                            transcript_file,
                            metadata
                        )
                        logger.info("Transcript metadata saved to database")
                    except Exception as db_error:
                        logger.error(f"Error saving transcript to database: {db_error}")
                
                return transcript_file
                
            except Exception as e:
                logger.error(f"Error transcribing audio: {e}")
                return None
        except Exception as e:
            logger.error(f"Error processing recording: {e}")
            return None
    
    async def get_session_transcripts(self, guild_id, session_id=None):
        """Get transcript(s) for a guild session"""
        try:
            # First check database if available
            if hasattr(self.bot, 'db') and self.bot.db:
                try:
                    db_transcripts = self.bot.db.get_transcripts(guild_id)
                    if db_transcripts:
                        return db_transcripts
                except Exception as db_error:
                    logger.warning(f"Could not get transcripts from database: {db_error}")
            
            # Fall back to file system
            session_path = None
            
            if session_id:
                # Get specific session
                session_path = f"data/voice/sessions/guild_{guild_id}/{session_id}"
            else:
                # Get guild sessions directory
                session_path = f"data/voice/sessions/guild_{guild_id}"
            
            # Make sure the path exists
            if not os.path.exists(session_path):
                os.makedirs(session_path, exist_ok=True)
                return []
            
            # Find transcript files
            transcripts = []
            for root, dirs, files in os.walk(session_path):
                for file in files:
                    if file.endswith("_transcript.txt") or file.endswith("_timestamped.txt"):
                        transcript_path = os.path.join(root, file)
                        timestamp = os.path.getmtime(transcript_path)
                        transcripts.append({
                            "path": transcript_path,
                            "filename": file,
                            "timestamp": timestamp,
                            "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        })
            
            # Sort by timestamp (newest first)
            transcripts.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return transcripts
        except Exception as e:
            logger.error(f"Error getting session transcripts: {e}")
            return []
    
    async def read_transcript(self, transcript_path):
        """Read a transcript file"""
        try:
            if not os.path.exists(transcript_path):
                return None
                
            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return content
        except Exception as e:
            logger.error(f"Error reading transcript: {e}")
            return None
    
    def is_connected(self, guild_id):
        """Check if connected to voice in a guild"""
        if not hasattr(self, 'voice_clients') or self.voice_clients is None:
            return False
        voice_client = self.voice_clients.get(guild_id)
        return voice_client is not None and voice_client.is_connected()
    
    def is_recording(self, guild_id):
        """Check if recording in a guild"""
        if not hasattr(self, 'recording_sessions') or self.recording_sessions is None:
            return False
        return guild_id in self.recording_sessions
    
    def get_connected_guilds(self):
        """Get a list of connected guild IDs"""
        if not hasattr(self, 'voice_clients') or self.voice_clients is None:
            return []
        return list(self.voice_clients.keys())