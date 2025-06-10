"""
Bishop Bot - Alternative Speech Processor
Last updated: 2025-05-31 15:23:46 UTC by Bioku87

This module provides an alternative speech processing implementation.
It can be used as a fallback or for specific languages/accents.
"""
import os
import logging
import asyncio
import tempfile
from datetime import datetime
import warnings

# Suppress warnings from imported libraries
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger('bishop_bot.voice.speech_alt')

class AlternativeSpeechProcessor:
    """Alternative speech processor implementation using various backends"""
    
    def __init__(self):
        """Initialize the alternative speech processor"""
        self.available_backends = self._detect_backends()
        logger.info(f"Alternative speech processor initialized with backends: {', '.join(self.available_backends) if self.available_backends else 'None'}")
        
    def _detect_backends(self):
        """Detect available speech recognition backends"""
        backends = []
        
        # Check for Whisper
        try:
            import whisper
            backends.append("whisper")
        except ImportError:
            pass
            
        # Check for Vosk
        try:
            from vosk import Model, KaldiRecognizer
            
            model_path = os.path.join("data", "voice", "models", "vosk-model-small-en-us-0.15")
            if os.path.exists(model_path):
                backends.append("vosk")
        except ImportError:
            pass
            
        # Check for Azure Speech
        try:
            import azure.cognitiveservices.speech as speechsdk
            if os.environ.get("AZURE_SPEECH_KEY"):
                backends.append("azure")
        except ImportError:
            pass
            
        return backends
        
    async def process_audio(self, audio_file):
        """Process audio file using available backends"""
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return None
            
        # Try all available backends in order of preference
        for backend in self.available_backends:
            try:
                if backend == "whisper":
                    return await self._process_with_whisper(audio_file)
                elif backend == "vosk":
                    return await self._process_with_vosk(audio_file)
                elif backend == "azure":
                    return await self._process_with_azure(audio_file)
            except Exception as e:
                logger.error(f"Error processing with {backend}: {e}")
                
        # If we get here, all backends failed
        logger.warning("All alternative speech processing backends failed")
        return None
        
    async def _process_with_whisper(self, audio_file):
        """Process audio with OpenAI Whisper model"""
        import whisper
        
        # This runs in a separate thread to avoid blocking
        def _run_whisper():
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_file)
            return result["text"].strip()
            
        # Run in a thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, _run_whisper)
        
        logger.info(f"Whisper transcription: {text}")
        return text
        
    async def _process_with_vosk(self, audio_file):
        """Process audio with Vosk speech recognition"""
        import wave
        from vosk import Model, KaldiRecognizer
        import json
        
        model_path = os.path.join("data", "voice", "models", "vosk-model-small-en-us-0.15")
        
        if not os.path.exists(model_path):
            logger.error("Vosk model not found")
            return None
            
        def _run_vosk():
            model = Model(model_path)
            wf = wave.open(audio_file, "rb")
            
            # Check audio format
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                logger.error("Audio file must be WAV format mono PCM")
                return None
                
            # Create recognizer
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)
            
            # Process audio
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    if "text" in part_result and part_result["text"].strip():
                        results.append(part_result["text"])
                        
            # Get final result
            part_result = json.loads(rec.FinalResult())
            if "text" in part_result and part_result["text"].strip():
                results.append(part_result["text"])
                
            return " ".join(results)
            
        # Run in a thread pool
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, _run_vosk)
        
        logger.info(f"Vosk transcription: {text}")
        return text
        
    async def _process_with_azure(self, audio_file):
        """Process audio with Azure Speech Services"""
        import azure.cognitiveservices.speech as speechsdk
        
        # Get credentials
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION", "westus")
        
        if not key:
            logger.error("Azure Speech key not found in environment variables")
            return None
            
        # Define result holder
        result_text = [None]
        done = asyncio.Event()
        
        def _recognized_cb(evt):
            result_text[0] = evt.result.text
            done.set()
            
        def _canceled_cb(evt):
            logger.warning(f"Azure recognition canceled: {evt.result.reason}")
            done.set()
            
        def _run_azure():
            # Configure speech service
            speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
            
            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            
            # Connect callbacks
            recognizer.recognized.connect(_recognized_cb)
            recognizer.canceled.connect(_canceled_cb)
            
            # Start recognition
            recognizer.start_continuous_recognition()
            
            return recognizer
            
        # Run in a thread pool
        loop = asyncio.get_running_loop()
        recognizer = await loop.run_in_executor(None, _run_azure)
        
        # Wait for completion (with timeout)
        try:
            await asyncio.wait_for(done.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Azure speech recognition timed out")
        finally:
            await loop.run_in_executor(None, recognizer.stop_continuous_recognition)
        
        logger.info(f"Azure transcription: {result_text[0]}")
        return result_text[0]