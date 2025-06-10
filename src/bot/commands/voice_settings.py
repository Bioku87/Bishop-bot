"""
Bishop Bot - Voice Settings Commands
Last updated: 2025-05-31 15:45:38 UTC by Bioku87

Commands for configuring voice settings and profiles.
"""
import discord
from discord import app_commands
import logging

logger = logging.getLogger('bishop_bot.commands.voice_settings')

async def setup(bot):
    """Set up voice settings commands"""
    
    @bot.tree.command(name="voiceset", description="Set your voice recognition preferences")
    async def voice_set_command(interaction: discord.Interaction, language: str = "en-US"):
        """Set voice recognition preferences"""
        # This is just a placeholder - actual implementation will use voice_profile_manager
        await interaction.response.send_message(f"Voice preferences set to language: {language}")
    
    logger.info("Voice settings commands registered")