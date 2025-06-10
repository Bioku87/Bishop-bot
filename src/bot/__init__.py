"""
Bishop Bot - Bot Initialization
Last updated: 2025-06-01 12:58:55 UTC by Bioku87
"""
import os
import sys
import logging
import asyncio
import datetime
import discord
from discord.ext import commands as discord_commands
from typing import Dict, List, Any, Optional

# Set up logger
logger = logging.getLogger('bishop_bot.bot')

# Import commands registration function
try:
    from .commands import register_commands
    logger.info("Successfully imported command registration")
except ImportError as e:
    logger.error(f"Could not import commands: {e}")
    # Define a stub function if the real one isn't available
    async def register_commands(bot):
        logger.warning("Using stub command registration")
        return False

class BishopBot(discord_commands.Bot):
    """Main Bishop Bot class"""
    
    def __init__(self, command_prefix='/', description="Bishop Bot", **options):
        """Initialize the bot"""
        # Configure intents
        intents = discord.Intents.all()
        
        # Initialize the bot
        super().__init__(command_prefix=command_prefix, description=description, intents=intents, **options)
        
        # Store bot uptime
        self.start_time = discord.utils.utcnow()
        
        # Bot state
        self.ready = False
        self.synced = False
        
        # Dictionary to track component initialization success
        self.initialized_components = {}
        
        # Initialize components
        self._initialize_components()
        
        logger.info("BishopBot class initialized")
    
    def _initialize_components(self):
        """Initialize bot components"""
        # Initialize database component
        try:
            logger.info("Initializing database component...")
            
            # Add src directory to path to help with imports
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
                
            try:
                from database.manager import DatabaseManager
                
                # Initialize the database
                self.db = DatabaseManager()
                self.initialized_components["database"] = True
                
                logger.info("Database component initialized successfully")
            except ImportError as import_error:
                logger.warning(f"Database manager import failed: {import_error}")
                
                # Create a minimal database
                db_path = "data/database"
                os.makedirs(db_path, exist_ok=True)
                
                # Create a simple SQLite DB file
                import sqlite3
                conn = sqlite3.connect(f"{db_path}/bishop.db")
                cursor = conn.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_data (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                ''')
                conn.commit()
                conn.close()
                
                # Create a minimal database manager
                class MinimalDatabaseManager:
                    def get_value(self, key):
                        return None
                        
                    def set_value(self, key, value):
                        return False
                        
                    def close(self):
                        pass
                
                self.db = MinimalDatabaseManager()
                self.initialized_components["database"] = True
                logger.info("Minimal database initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            self.initialized_components["database"] = False
        
        # Initialize Voice Manager with ultra safe approach
        try:
            logger.info("Initializing voice manager...")
            # Create a simple object with required methods if import fails
            self.voice_manager = None
            self.initialized_components["voice"] = False
            
            # Import the voice manager with manual exception handling
            try:
                # Add src directory to path to help with imports (if not added already)
                src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if src_path not in sys.path:
                    sys.path.insert(0, src_path)
                    
                # Try to import
                from voice.manager import VoiceManager
                
                # Create instance with safe initialization
                self.voice_manager = VoiceManager(self)
                self.initialized_components["voice"] = True
                logger.info("Voice manager initialized successfully")
            except ImportError as e:
                logger.warning(f"Voice manager import failed: {e}")
            except Exception as e:
                logger.error(f"Error creating voice manager instance: {e}")
        except Exception as e:
            logger.error(f"Error in voice manager initialization block: {e}")
            # Ensure voice_manager attribute exists even if everything fails
            if not hasattr(self, 'voice_manager') or self.voice_manager is None:
                class MinimalVoiceManager:
                    def __init__(self):
                        self.voice_clients = {}
                        self.recording_sessions = {}
                    
                    def get_connected_guilds(self):
                        return []
                    
                    def is_connected(self, guild_id):
                        return False
                    
                    def is_recording(self, guild_id):
                        return False
                    
                    async def join_voice_channel(self, channel):
                        return False
                        
                    async def disconnect_from_guild(self, guild_id):
                        return False
                        
                    async def start_recording(self, guild_id):
                        return False
                        
                    async def stop_recording(self, guild_id):
                        return False
                        
                    async def get_session_transcripts(self, guild_id, session_id=None):
                        return []
                        
                    async def read_transcript(self, path):
                        return "Transcript not available"
                
                self.voice_manager = MinimalVoiceManager()
                self.initialized_components["voice"] = False
                logger.info("Created fallback minimal voice manager")
        
        # Initialize Audio Manager
        try:
            logger.info("Initializing audio manager...")
            # Audio manager import (using the path we already added)
            from audio.manager import AudioManager
            self.audio_manager = AudioManager(self)
            self.initialized_components["audio"] = True
            logger.info("Audio manager initialized successfully")
        except ImportError as e:
            logger.warning(f"Audio manager not available: {e}")
            
            # Create a minimal audio manager
            class MinimalAudioManager:
                def __init__(self, bot):
                    self.bot = bot
                    self.voice_clients = {}
                    
                async def play_sound(self, guild_id, sound_name, category="Default"):
                    return False
                    
                async def stop_playback(self, guild_id):
                    return False
                    
                def get_sounds_in_category(self, category):
                    return []
                    
                async def disconnect_from_guild(self, guild_id):
                    return False
            
            self.audio_manager = MinimalAudioManager(self)
            self.initialized_components["audio"] = False
            logger.info("Created fallback minimal audio manager")
        except Exception as e:
            logger.error(f"Error initializing audio manager: {e}")
            self.audio_manager = None
            self.initialized_components["audio"] = False
    
    async def setup_hook(self):
        """Set up the bot before connecting to Discord"""
        try:
            # Register commands
            await register_commands(self)
            
            # We'll defer setting presence until we're connected
            # The error "Failed to set bot presence: 'NoneType' object has no attribute 'change_presence'"
            # happens because we try to set presence before the bot is connected
            logger.info("Bot setup completed - will set presence after connection")
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")
            logger.error("Bot will continue with limited functionality")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        if self.ready:
            logger.info("Bot reconnected")
            return
            
        self.ready = True
        
        # Set presence now that we're connected
        try:
            activity = discord.Activity(type=discord.ActivityType.listening, name="/help")
            await self.change_presence(activity=activity, status=discord.Status.online)
            logger.info("Bot presence set successfully")
        except Exception as e:
            logger.error(f"Error setting bot presence in on_ready: {e}")
        
        logger.info(f"Connected as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f"Connected to guild: {guild.name} (ID: {guild.id})")
            
        print(f"\nBishop Bot is ready! Connected as {self.user}")
        print(f"Connected to {len(self.guilds)} guilds")
        print("=" * 50)
    
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates"""
        try:
            # If the bot is left alone in a voice channel, leave
            if before.channel is not None and member.id != self.user.id:
                # Check if bot is in the channel
                bot_in_channel = False
                for m in before.channel.members:
                    if m.id == self.user.id:
                        bot_in_channel = True
                        break
                
                if bot_in_channel:
                    # Check if alone
                    alone = True
                    for m in before.channel.members:
                        if not m.bot and m.id != self.user.id:
                            alone = False
                            break
                    
                    # Disconnect if alone
                    if alone:
                        logger.info(f"Left alone in voice channel {before.channel.name}, disconnecting")
                        
                        # Disconnect voice manager
                        if hasattr(self, 'voice_manager') and self.voice_manager:
                            await self.voice_manager.disconnect_from_guild(before.channel.guild.id)
                        
                        # Disconnect audio manager
                        if hasattr(self, 'audio_manager') and self.audio_manager:
                            await self.audio_manager.disconnect_from_guild(before.channel.guild.id)
        except Exception as e:
            logger.error(f"Error in voice state update: {e}")
    
    async def on_application_command_error(self, interaction, error):
        """Handle errors in slash commands"""
        try:
            if isinstance(error, discord_commands.errors.CommandOnCooldown):
                await interaction.response.send_message(
                    f"This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.",
                    ephemeral=True
                )
            elif isinstance(error, discord_commands.errors.MissingPermissions):
                await interaction.response.send_message(
                    "You don't have permission to use this command.",
                    ephemeral=True
                )
            else:
                logger.error(f"Command error: {error}")
                # Try to send an error message if possible
                try:
                    if interaction.response.is_done():
                        await interaction.followup.send(
                            f"An error occurred while processing your command: {str(error)}",
                            ephemeral=True
                        )
                    else:
                        await interaction.response.send_message(
                            f"An error occurred while processing your command: {str(error)}",
                            ephemeral=True
                        )
                except:
                    pass
        except Exception as e:
            logger.error(f"Error handling command error: {e}")
    
    async def on_message(self, message):
        """Process messages for prefix commands if needed"""
        # Don't respond to our own messages
        if message.author.id == self.user.id:
            return
        
        # Process commands for legacy prefix commands if needed
        await self.process_commands(message)
    
    async def on_guild_join(self, guild):
        """Handle joining a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Send welcome message to the first available text channel
        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    embed = discord.Embed(
                        title="Thanks for adding Bishop Bot!",
                        description="Hello! I'm Bishop, a bot designed for tabletop RPG sessions with voice and audio features.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="Getting Started",
                        value="Type `/help` to see available commands.",
                        inline=False
                    )
                    embed.set_footer(text="Made by Bioku87")
                    
                    await channel.send(embed=embed)
                    break
        except Exception as e:
            logger.error(f"Error sending welcome message to guild {guild.name}: {e}")
    
    def get_uptime(self):
        """Get the bot's uptime as a string"""
        delta = discord.utils.utcnow() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        if days:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            return f"{hours}h {minutes}m {seconds}s"
    
    def close(self):
        """Properly close the bot and its components"""
        # Close database if available
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
                logger.info("Database closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        # Call parent close method
        super().close()

# Export the BishopBot class
__all__ = ['BishopBot']