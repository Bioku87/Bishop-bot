"""
Bishop Bot - Speech Processor
Last updated: 2025-05-31 15:23:46 UTC by Bioku87

This module processes speech and converts it to text.
"""
import os
import io
import wave
import logging
import time
import asyncio
import tempfile
from datetime import datetime

import speech_recognition as sr
from discord.opus import Encoder as OpusEncoder

logger = logging.getLogger('bishop_bot.voice.speech_processor')

class SpeechProcessor:
    """Handles speech-to-text conversion using various APIs"""
    
    def __init__(self, config=None):
        """Initialize the speech processor"""
        self.recognizer = sr.Recognizer()
        self.config = config or {}
        
        # Default settings
        self.language = self.config.get('language', 'en-US')
        self.sample_rate = 16000  # Hz
        self.channels = 1  # Mono
        self.width = 2  # 16-bit
        
        # Transcription session
        self.current_session = None
        self.session_start_time = None
        
        # Performance tracking
        self.processed_chunks = 0
        self.successful_transcriptions = 0
        
        logger.info("Speech processor initialized")
    
    def start_session(self, name=None):
        """Start a new transcription session"""
        if self.current_session:
            logger.warning("Stopping existing session to start new one")
            self.stop_session()
            
        session_id = int(time.time())
        session_name = name if name else f"Session_{session_id}"
        
        self.current_session = {
            "id": session_id,
            "name": session_name,
            "start_time": datetime.now(),
            "lines": [],
            "speakers": set(),
            "processed_audio_seconds": 0,
            "last_update": datetime.now()
        }
        
        self.session_start_time = time.time()
        logger.info(f"Started transcription session: {session_name}")
        
        return self.current_session
    
    def stop_session(self):
        """Stop the current transcription session"""
        if not self.current_session:
            logger.warning("No active session to stop")
            return None
            
        session_duration = time.time() - self.session_start_time
        self.current_session["duration"] = session_duration
        self.current_session["end_time"] = datetime.now()
        
        logger.info(f"Stopped transcription session: {self.current_session['name']}")
        logger.info(f"Session duration: {session_duration:.2f} seconds")
        logger.info(f"Lines transcribed: {len(self.current_session['lines'])}")
        
        result = self.current_session
        self.current_session = None
        self.session_start_time = None
        
        return result
    
    def get_session_stats(self):
        """Get statistics for the current session"""
        if not self.current_session:
            return None
            
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        return {
            "name": self.current_session["name"],
            "duration": session_duration,
            "lines": len(self.current_session["lines"]),
            "speakers": len(self.current_session["speakers"]),
            "processed_audio_seconds": self.current_session["processed_audio_seconds"]
        }
    
    async def process_audio(self, audio_data, user_id, username):
        """Process raw audio data and convert to text"""
        if not audio_data or len(audio_data) < 1000:  # Too short to process
            return None
            
        try:
            # Track performance
            start_time = time.time()
            self.processed_chunks += 1
            
            # Convert opus data to WAV
            pcm_data = self._decode_opus(audio_data)
            
            if not pcm_data:
                return None
                
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_filename = temp_wav.name
                self._write_wav(temp_filename, pcm_data)
            
            try:
                # Process with speech recognition
                with sr.AudioFile(temp_filename) as source:
                    audio = self.recognizer.record(source)
                    
                    # Try Google Speech Recognition (requires internet)
                    text = await self._recognize_google(audio)
                    
                    if not text and os.path.getsize(temp_filename) > 5000:
                        # Fall back to other methods if Google fails
                        try:
                            from . import speech_alt
                            alt_processor = speech_alt.AlternativeSpeechProcessor()
                            text = await alt_processor.process_audio(temp_filename)
                        except Exception as e:
                            logger.error(f"Error in alternative speech processing: {e}")
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {e}")
            
            # Process results
            if text:
                self.successful_transcriptions += 1
                logger.debug(f"Transcription successful: '{text}'")
                
                # Add to current session if active
                if self.current_session:
                    self.current_session["lines"].append({
                        "timestamp": datetime.now().isoformat(),
                        "user_id": user_id,
                        "username": username,
                        "text": text
                    })
                    self.current_session["speakers"].add(user_id)
                    self.current_session["last_update"] = datetime.now()
                    self.current_session["processed_audio_seconds"] += len(pcm_data) / self.sample_rate / self.channels / self.width
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": time.time() - start_time
                }
            
            return None
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    
    async def _recognize_google(self, audio):
        """Recognize speech using Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
        except sr.UnknownValueError:
            logger.debug("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except Exception as e:
            logger.error(f"Error in Google speech recognition: {e}")
            return None
    
    def _decode_opus(self, opus_data):
        """Decode Opus data to PCM"""
        try:
            # Create a frame buffer
            buffer = io.BytesIO()
            
            # Process each packet
            for i in range(0, len(opus_data), OpusEncoder.FRAME_SIZE):
                chunk = opus_data[i:i+OpusEncoder.FRAME_SIZE]
                if len(chunk) == OpusEncoder.FRAME_SIZE:
                    # Decode opus frame
                    try:
                        decoded = OpusEncoder.decode_float(chunk, channels=1)
                        buffer.write(decoded)
                    except Exception as e:
                        logger.error(f"Error decoding opus frame: {e}")
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error decoding opus data: {e}")
            return None
    
    def _write_wav(self, filename, pcm_data):
        """Write PCM data to a WAV file"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(pcm_data)
        except Exception as e:
            logger.error(f"Error writing WAV file: {e}")
            
    def export_session(self, session=None, format_type="txt"):
        """Export the session to a file"""
        export_session = session or self.current_session
        
        if not export_session:
            logger.warning("No session to export")
            return None
            
        try:
            # Generate export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = export_session["name"].replace(" ", "_")
            filename = f"transcript_{session_name}_{timestamp}.{format_type}"
            export_dir = "data/exports"
            os.makedirs(export_dir, exist_ok=True)
            filepath = os.path.join(export_dir, filename)
            
            # Generate export content
            content = self._format_session_export(export_session, format_type)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
                
            logger.info(f"Exported session to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return None
    
    def _format_session_export(self, session, format_type="txt"):
        """Format session data for export"""
        if format_type == "txt":
            # Create text format
            start_time = session.get("start_time", datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            
            content = [
                f"Transcript: {session['name']}",
                f"Date: {start_time}",
                f"Lines: {len(session['lines'])}",
                f"Speakers: {len(session['speakers'])}",
                "=" * 40,
                ""
            ]
            
            # Add transcript lines
            for line in session["lines"]:
                timestamp = datetime.fromisoformat(line["timestamp"]).strftime("%H:%M:%S")
                content.append(f"[{timestamp}] {line['username']}: {line['text']}")
            
            return "\n".join(content)
            
        else:
            # Unsupported format
            return f"Export format {format_type} not supported"

# Create singleton instance
speech_processor = SpeechProcessor()