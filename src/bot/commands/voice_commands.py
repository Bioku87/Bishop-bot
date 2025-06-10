"""
Bishop Bot - Voice Commands (Simplified)
Last updated: 2025-05-31 23:13:05 UTC by Bioku87
"""
import discord
import logging
import os
from discord import app_commands
from discord.ext import commands
from datetime import datetime

logger = logging.getLogger('bishop_bot.commands.voice')

async def register_voice_commands(bot):
    """Register voice-related commands"""
    
    @bot.tree.command(name="join", description="Join a voice channel")
    @app_commands.describe(channel="The voice channel to join (optional, will use your current channel if not specified)")
    async def join_command(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        try:
            # If no channel is specified, use the user's current channel
            if channel is None:
                if interaction.user.voice and interaction.user.voice.channel:
                    channel = interaction.user.voice.channel
                else:
                    await interaction.response.send_message("You need to specify a channel or be in a voice channel.", ephemeral=True)
                    return
            
            # Join the channel
            await interaction.response.defer(ephemeral=True)
            
            # Join with voice manager
            success = False
            if hasattr(bot, 'voice_manager'):
                success = await bot.voice_manager.join_voice_channel(channel)
            
            # Also connect audio manager to the same channel
            if hasattr(bot, 'audio_manager'):
                success = await bot.audio_manager.join_voice_channel(channel)
            
            if success:
                await interaction.followup.send(f"Joined voice channel: {channel.name}", ephemeral=False)
            else:
                await interaction.followup.send("Failed to join voice channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in join command: {e}")
            await interaction.followup.send("An error occurred while joining the voice channel.", ephemeral=True)
    
    @bot.tree.command(name="leave", description="Leave the current voice channel")
    async def leave_command(interaction: discord.Interaction):
        try:
            success = False
            
            # Disconnect voice manager if available
            if hasattr(bot, 'voice_manager'):
                if bot.voice_manager.is_connected(interaction.guild_id):
                    await bot.voice_manager.disconnect_from_guild(interaction.guild_id)
                    success = True
                    
            # Disconnect audio manager if available
            if hasattr(bot, 'audio_manager'):
                if bot.audio_manager.is_connected(interaction.guild_id):
                    await bot.audio_manager.disconnect_from_guild(interaction.guild_id)
                    success = True
                    
            if success:
                await interaction.response.send_message("Left the voice channel.")
            else:
                await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in leave command: {e}")
            await interaction.response.send_message("An error occurred while leaving the voice channel.", ephemeral=True)
    
    @bot.tree.command(name="record", description="Start recording the voice channel")
    async def record_command(interaction: discord.Interaction):
        try:
            # Get voice manager from bot
            if not hasattr(bot, 'voice_manager'):
                await interaction.response.send_message("Voice recording is not available.", ephemeral=True)
                return
                
            voice_manager = bot.voice_manager
            
            # Check if the bot is in a voice channel in this guild
            if not voice_manager.is_connected(interaction.guild_id):
                await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
                return
            
            # Check if already recording
            if voice_manager.is_recording(interaction.guild_id):
                await interaction.response.send_message("Already recording in this channel.", ephemeral=True)
                return
            
            # Generate a session ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            channel_name = interaction.channel.name if interaction.channel else "unknown"
            session_id = f"session_{timestamp}_{channel_name}"
            
            # Start recording
            success = await voice_manager.start_recording(interaction.guild_id, session_id)
            
            if success:
                embed = discord.Embed(
                    title="Recording Started",
                    description="Started recording the voice channel.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Session ID", value=session_id)
                embed.add_field(name="Started by", value=interaction.user.mention)
                embed.set_footer(text="Use /stoprecord to stop recording")
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to start recording.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in record command: {e}")
            await interaction.response.send_message("An error occurred while starting the recording.", ephemeral=True)
    
    @bot.tree.command(name="stoprecord", description="Stop recording the voice channel")
    async def stop_record_command(interaction: discord.Interaction):
        try:
            # Get voice manager from bot
            if not hasattr(bot, 'voice_manager'):
                await interaction.response.send_message("Voice recording is not available.", ephemeral=True)
                return
                
            voice_manager = bot.voice_manager
            
            # Check if the bot is recording in this guild
            if not voice_manager.is_recording(interaction.guild_id):
                await interaction.response.send_message("I'm not currently recording.", ephemeral=True)
                return
            
            # Stop recording
            await interaction.response.defer(ephemeral=False)
            success = await voice_manager.stop_recording(interaction.guild_id)
            
            if success:
                embed = discord.Embed(
                    title="Recording Stopped",
                    description="Stopped recording and processing transcript...",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Stopped by", value=interaction.user.mention)
                embed.set_footer(text="Use /transcripts to view available transcripts")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Failed to stop recording.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in stop_record command: {e}")
            await interaction.followup.send("An error occurred while stopping the recording.", ephemeral=True)
    
    @bot.tree.command(name="transcripts", description="Get available session transcripts")
    async def transcripts_command(interaction: discord.Interaction):
        try:
            # Get voice manager from bot
            if not hasattr(bot, 'voice_manager'):
                await interaction.response.send_message("Voice transcription is not available.", ephemeral=True)
                return
                
            voice_manager = bot.voice_manager
            
            # Get available transcripts
            transcripts = await voice_manager.get_session_transcripts(interaction.guild_id)
            
            if not transcripts:
                await interaction.response.send_message("No transcripts found for this server.", ephemeral=True)
                return
            
            # Create embed with transcript list
            embed = discord.Embed(
                title="Available Transcripts",
                description=f"Found {len(transcripts)} transcript(s) for this server.",
                color=discord.Color.blue()
            )
            
            # Show most recent 10 transcripts
            for i, transcript in enumerate(transcripts[:10]):
                embed.add_field(
                    name=f"{i+1}. {transcript['filename']}",
                    value=f"Date: {transcript['date']}",
                    inline=False
                )
            
            embed.set_footer(text="Use /readtranscript <number> to read a transcript")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in transcripts command: {e}")
            await interaction.response.send_message("An error occurred while getting the transcripts.", ephemeral=True)
    
    @bot.tree.command(name="readtranscript", description="Read a transcript by number")
    @app_commands.describe(number="The transcript number from /transcripts")
    async def read_transcript_command(interaction: discord.Interaction, number: int):
        try:
            # Get voice manager from bot
            if not hasattr(bot, 'voice_manager'):
                await interaction.response.send_message("Voice transcription is not available.", ephemeral=True)
                return
                
            voice_manager = bot.voice_manager
            
            # Get available transcripts
            transcripts = await voice_manager.get_session_transcripts(interaction.guild_id)
            
            if not transcripts:
                await interaction.response.send_message("No transcripts found for this server.", ephemeral=True)
                return
            
            # Check if number is valid
            if number < 1 or number > len(transcripts):
                await interaction.response.send_message(f"Invalid transcript number. Choose between 1 and {len(transcripts)}.", ephemeral=True)
                return
            
            # Get the transcript
            transcript = transcripts[number - 1]
            transcript_content = await voice_manager.read_transcript(transcript['path'])
            
            if not transcript_content:
                await interaction.response.send_message("Failed to read transcript.", ephemeral=True)
                return
            
            # Limit content length for Discord
            if len(transcript_content) > 1900:
                # Create a text file for the transcript
                filename = f"Transcript_{number}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(transcript_content)
                
                # Send as file
                file = discord.File(filename)
                await interaction.response.send_message(f"Transcript #{number} - {transcript['filename']}", file=file)
                
                # Clean up file
                try:
                    os.remove(filename)
                except:
                    pass
            else:
                # Send as message
                await interaction.response.send_message(f"**Transcript #{number} - {transcript['filename']}**\n```\n{transcript_content}\n```")
        except Exception as e:
            logger.error(f"Error in read_transcript command: {e}")
            await interaction.response.send_message("An error occurred while reading the transcript.", ephemeral=True)
    
    logger.info("Voice commands registered")
    return True