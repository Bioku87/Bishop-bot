"""
Bishop Bot - Character Registration Commands
Last updated: 2025-05-31 15:45:38 UTC by Bioku87

Commands for character registration and management.
"""
import discord
from discord import app_commands
import logging

logger = logging.getLogger('bishop_bot.commands.unified')

async def setup(bot):
    """Set up unified commands"""
    
    @bot.tree.command(name="register", description="Register your character")
    async def register_command(interaction: discord.Interaction, name: str):
        """Register a character"""
        # This is just a placeholder - actual implementation will use character_manager
        await interaction.response.send_message(f"Character {name} registered!")
    
    logger.info("Character commands registered")