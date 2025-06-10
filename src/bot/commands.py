"""
Bishop Bot - Command Registration
Last updated: 2025-06-01 06:15:40 UTC by Bioku87
"""
import logging
import discord
from discord import app_commands
from typing import List, Optional, Dict, Any
import os
import asyncio

logger = logging.getLogger('bishop_bot.commands')

# Store registered commands for reference
registered_commands = []

async def register_commands(bot):
    """Register all bot commands with Discord"""
    logger.info("Registering bot commands...")
    
    # Clear any existing commands to avoid duplicates
    registered_commands.clear()
    
    # Register general commands
    register_general_commands(bot)
    
    # Register voice commands
    register_voice_commands(bot)
    
    # Register audio commands
    register_audio_commands(bot)
    
    # Register admin commands
    register_admin_commands(bot)
    
    # Sync commands with Discord
    logger.info("Syncing commands with Discord...")
    try:
        await bot.tree.sync()
        logger.info("Command sync complete!")
    except Exception as e:
        logger.error(f"Command sync failed: {e}")
        raise
    
    return True

def register_general_commands(bot):
    """Register general utility commands"""
    
    @bot.tree.command(name="help", description="Show available commands")
    async def help_command(interaction: discord.Interaction):
        """Show help information about the bot and available commands"""
        embed = discord.Embed(
            title="Bishop Bot Help",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        
        # General Commands
        embed.add_field(
            name="General Commands",
            value=(
                "`/help` - Show this help message\n"
                "`/info` - Show bot information\n"
                "`/ping` - Check bot latency"
            ),
            inline=False
        )
        
        # Voice Commands
        embed.add_field(
            name="Voice Commands",
            value=(
                "`/join` - Join a voice channel\n"
                "`/leave` - Leave the voice channel\n"
                "`/record` - Start recording the voice channel\n"
                "`/stoprecord` - Stop recording\n"
                "`/transcripts` - List available transcripts\n"
                "`/readtranscript <number>` - Read a specific transcript"
            ),
            inline=False
        )
        
        # Audio Commands
        embed.add_field(
            name="Audio Commands",
            value=(
                "`/play <sound> [category]` - Play a sound from the soundboard\n"
                "`/stop` - Stop audio playback\n"
                "`/soundboard [category]` - Show available sounds"
            ),
            inline=False
        )
        
        # Admin Commands
        embed.add_field(
            name="Admin Commands",
            value=(
                "`/sync` - Force sync commands with Discord (Admin Only)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Made by Bioku87")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    registered_commands.append("help")
    
    @bot.tree.command(name="info", description="Show bot information")
    async def info_command(interaction: discord.Interaction):
        """Show information about the bot"""
        embed = discord.Embed(
            title="About Bishop Bot",
            description="Discord bot for tabletop RPG sessions with audio and voice features.",
            color=discord.Color.blue()
        )
        
        # Add bot information
        embed.add_field(name="Version", value="v0.1.0", inline=True)
        embed.add_field(name="Created By", value="Bioku87", inline=True)
        
        # Add uptime if available
        if hasattr(bot, 'get_uptime'):
            embed.add_field(name="Uptime", value=bot.get_uptime(), inline=True)
        
        # Add system information
        embed.add_field(name="Connected Servers", value=str(len(bot.guilds)), inline=True)
        
        # Add component status
        components = []
        if hasattr(bot, 'initialized_components'):
            for component, status in bot.initialized_components.items():
                components.append(f"{component.capitalize()}: {'✅' if status else '❌'}")
        
        if components:
            embed.add_field(name="Components", value="\n".join(components), inline=False)
        
        embed.set_footer(text=f"Discord ID: {bot.user.id}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    registered_commands.append("info")
    
    @bot.tree.command(name="ping", description="Check bot latency")
    async def ping_command(interaction: discord.Interaction):
        """Check the bot's latency to Discord servers"""
        latency = round(bot.latency * 1000)  # Convert to ms
        await interaction.response.send_message(f"Pong! 🏓\nBot latency: {latency}ms", ephemeral=True)
    
    registered_commands.append("ping")

def register_voice_commands(bot):
    """Register voice-related commands"""
    
    @bot.tree.command(name="join", description="Join a voice channel")
    @app_commands.describe(channel="The voice channel to join")
    async def join_command(interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None):
        """Join a voice channel"""
        # Defer the response to give us time to process
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        # If no channel specified, use the user's current channel
        if channel is None:
            if not interaction.user.voice:
                await interaction.followup.send("You need to be in a voice channel or specify a channel to join.", ephemeral=True)
                return
            channel = interaction.user.voice.channel
        
        # Join the voice channel
        success = await bot.voice_manager.join_voice_channel(channel)
        
        if success:
            await interaction.followup.send(f"Joined voice channel: {channel.name}", ephemeral=True)
        else:
            await interaction.followup.send(f"Failed to join voice channel: {channel.name}", ephemeral=True)
    
    registered_commands.append("join")
    
    @bot.tree.command(name="leave", description="Leave the voice channel")
    async def leave_command(interaction: discord.Interaction):
        """Leave the current voice channel"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Check if connected
        if not bot.voice_manager.is_connected(guild_id):
            await interaction.followup.send("I'm not connected to a voice channel.", ephemeral=True)
            return
        
        # Leave the voice channel
        success = await bot.voice_manager.disconnect_from_guild(guild_id)
        
        if success:
            await interaction.followup.send("Left the voice channel.", ephemeral=True)
        else:
            await interaction.followup.send("Failed to leave the voice channel.", ephemeral=True)
    
    registered_commands.append("leave")
    
    @bot.tree.command(name="record", description="Start recording the voice channel")
    async def record_command(interaction: discord.Interaction):
        """Start recording the current voice channel"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Check if connected
        if not bot.voice_manager.is_connected(guild_id):
            await interaction.followup.send("I need to be in a voice channel first. Use `/join` to add me.", ephemeral=True)
            return
        
        # Check if already recording
        if bot.voice_manager.is_recording(guild_id):
            await interaction.followup.send("Already recording in this channel. Use `/stoprecord` to stop.", ephemeral=True)
            return
        
        # Start recording
        success = await bot.voice_manager.start_recording(guild_id)
        
        if success:
            await interaction.followup.send("📹 Started recording the voice channel!", ephemeral=False)  # Visible to everyone
        else:
            await interaction.followup.send("Failed to start recording.", ephemeral=True)
    
    registered_commands.append("record")
    
    @bot.tree.command(name="stoprecord", description="Stop recording the voice channel")
    async def stoprecord_command(interaction: discord.Interaction):
        """Stop recording the current voice channel"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Check if recording
        if not bot.voice_manager.is_recording(guild_id):
            await interaction.followup.send("Not currently recording.", ephemeral=True)
            return
        
        # Stop recording
        success = await bot.voice_manager.stop_recording(guild_id)
        
        if success:
            await interaction.followup.send("⏹️ Stopped recording. Transcribing audio...", ephemeral=False)  # Visible to everyone
        else:
            await interaction.followup.send("Failed to stop recording.", ephemeral=True)
    
    registered_commands.append("stoprecord")
    
    @bot.tree.command(name="transcripts", description="List available transcripts")
    async def transcripts_command(interaction: discord.Interaction):
        """List available transcripts for this server"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Get transcripts
        transcripts = await bot.voice_manager.get_session_transcripts(guild_id)
        
        if not transcripts:
            await interaction.followup.send("No transcripts found for this server.", ephemeral=True)
            return
        
        # Create embed with transcript list
        embed = discord.Embed(
            title="Available Transcripts",
            description="Use `/readtranscript <number>` to read a transcript.",
            color=discord.Color.blue()
        )
        
        for i, transcript in enumerate(transcripts[:10]):  # Show at most 10
            name = f"{i+1}. {transcript['date']}"
            value = f"File: {transcript['filename']}"
            embed.add_field(name=name, value=value, inline=False)
        
        if len(transcripts) > 10:
            embed.set_footer(text=f"Showing 10 of {len(transcripts)} transcripts.")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    registered_commands.append("transcripts")
    
    @bot.tree.command(name="readtranscript", description="Read a specific transcript")
    @app_commands.describe(number="The transcript number from the list")
    async def readtranscript_command(interaction: discord.Interaction, number: int):
        """Read a specific transcript"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if voice manager is available
        if not hasattr(bot, 'voice_manager') or bot.voice_manager is None:
            await interaction.followup.send("Voice features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Get transcripts
        transcripts = await bot.voice_manager.get_session_transcripts(guild_id)
        
        if not transcripts:
            await interaction.followup.send("No transcripts found for this server.", ephemeral=True)
            return
        
        # Check if number is valid
        if number < 1 or number > len(transcripts):
            await interaction.followup.send(f"Invalid transcript number. Please choose between 1 and {len(transcripts)}.", ephemeral=True)
            return
        
        # Get the transcript
        transcript = transcripts[number-1]
        
        # Read transcript content
        content = await bot.voice_manager.read_transcript(transcript['path'])
        
        if not content:
            await interaction.followup.send("Failed to read transcript.", ephemeral=True)
            return
        
        # Create embed for transcript
        embed = discord.Embed(
            title=f"Transcript: {transcript['date']}",
            description="Session transcript from voice recording",
            color=discord.Color.blue()
        )
        
        # Break content into chunks if needed (Discord has a limit of 4096 chars per field)
        # We'll take the start and end of the transcript
        if len(content) > 4000:
            # First 1500 chars
            embed.add_field(name="Beginning", value=content[:1500], inline=False)
            # Last 1500 chars
            embed.add_field(name="End", value=content[-1500:], inline=False)
            embed.add_field(name="Note", value="Transcript was too long to display in full. Check for the complete file.", inline=False)
        else:
            embed.add_field(name="Content", value=content, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    registered_commands.append("readtranscript")

def register_audio_commands(bot):
    """Register audio-related commands"""
    
    @bot.tree.command(name="play", description="Play a sound from the soundboard")
    @app_commands.describe(sound="The sound to play", category="The category of sounds (default: Default)")
    async def play_command(interaction: discord.Interaction, sound: str, category: str = "Default"):
        """Play a sound from the soundboard"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if audio manager is available
        if not hasattr(bot, 'audio_manager') or bot.audio_manager is None:
            await interaction.followup.send("Audio features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Check if in a voice channel
        if not hasattr(bot, 'voice_manager') or not bot.voice_manager.is_connected(guild_id):
            # Try to join the user's voice channel
            if not interaction.user.voice:
                await interaction.followup.send("I need to be in a voice channel first. Join a voice channel and use `/join`.", ephemeral=True)
                return
                
            channel = interaction.user.voice.channel
            success = await bot.voice_manager.join_voice_channel(channel)
            
            if not success:
                await interaction.followup.send("Failed to join your voice channel.", ephemeral=True)
                return
        
        # Play the sound
        try:
            await bot.audio_manager.play_sound(guild_id, sound, category)
            await interaction.followup.send(f"Playing sound: {sound} from category: {category}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to play sound: {str(e)}", ephemeral=True)
    
    registered_commands.append("play")
    
    @bot.tree.command(name="stop", description="Stop audio playback")
    async def stop_command(interaction: discord.Interaction):
        """Stop audio playback"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if audio manager is available
        if not hasattr(bot, 'audio_manager') or bot.audio_manager is None:
            await interaction.followup.send("Audio features are not currently available.", ephemeral=True)
            return
            
        guild_id = interaction.guild_id
        
        # Stop playback
        try:
            await bot.audio_manager.stop_playback(guild_id)
            await interaction.followup.send("Stopped audio playback.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to stop playback: {str(e)}", ephemeral=True)
    
    registered_commands.append("stop")
    
    @bot.tree.command(name="soundboard", description="Show available sounds")
    @app_commands.describe(category="The category of sounds to list (default: all)")
    async def soundboard_command(interaction: discord.Interaction, category: Optional[str] = None):
        """Show available sounds on the soundboard"""
        # Defer the response
        await interaction.response.defer(ephemeral=True)
        
        # Check if audio manager is available
        if not hasattr(bot, 'audio_manager') or bot.audio_manager is None:
            await interaction.followup.send("Audio features are not currently available.", ephemeral=True)
            return
        
        # Get available categories
        categories = []
        soundboard_dir = "data/audio/soundboard"
        
        if os.path.exists(soundboard_dir):
            categories = [d for d in os.listdir(soundboard_dir) if os.path.isdir(os.path.join(soundboard_dir, d))]
        
        if not categories:
            await interaction.followup.send("No sound categories available.", ephemeral=True)
            return
        
        if category is None:
            # Show a list of categories
            embed = discord.Embed(
                title="Soundboard Categories",
                description="Available sound categories:",
                color=discord.Color.blue()
            )
            
            for cat in sorted(categories):
                # Count sounds in each category
                cat_dir = os.path.join(soundboard_dir, cat)
                audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
                sounds = [f for f in os.listdir(cat_dir) if f.lower().endswith(audio_extensions)]
                
                embed.add_field(
                    name=cat,
                    value=f"{len(sounds)} sounds available",
                    inline=True
                )
            
            embed.set_footer(text="Use /soundboard <category> to see sounds in a specific category")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Show sounds in the selected category
            if category not in categories:
                await interaction.followup.send(f"Category '{category}' not found.", ephemeral=True)
                return
                
            # Get sounds in the category
            cat_dir = os.path.join(soundboard_dir, category)
            audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
            sounds = [os.path.splitext(f)[0] for f in os.listdir(cat_dir) if f.lower().endswith(audio_extensions)]
            
            if not sounds:
                await interaction.followup.send(f"No sounds found in category '{category}'.", ephemeral=True)
                return
                
            # Create embed with sound list
            embed = discord.Embed(
                title=f"Sounds in '{category}'",
                description=f"Use `/play <sound> {category}` to play a sound.",
                color=discord.Color.blue()
            )
            
            # Split sounds into multiple fields if needed
            sound_groups = [sounds[i:i+20] for i in range(0, len(sounds), 20)]
            
            for i, group in enumerate(sound_groups):
                embed.add_field(
                    name=f"Sounds {i*20+1}-{i*20+len(group)}",
                    value="• " + "\n• ".join(group),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    registered_commands.append("soundboard")

def register_admin_commands(bot):
    """Register admin-only commands"""
    
    @bot.tree.command(name="sync", description="Force sync commands with Discord (Admin Only)")
    async def sync_command(interaction: discord.Interaction):
        """Force sync commands with Discord - for admins only"""
        # Check if user is admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("This command is only for administrators.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Sync commands
            await bot.tree.sync()
            await interaction.followup.send("Commands synced successfully!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to sync commands: {str(e)}", ephemeral=True)
    
    registered_commands.append("sync")