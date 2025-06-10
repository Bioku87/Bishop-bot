"""
Bishop Bot - Basic Commands
Last updated: 2025-05-31 15:45:38 UTC by Bioku87

Basic utility commands for the bot.
"""
import discord
from discord import app_commands
import logging

logger = logging.getLogger('bishop_bot.commands.basic')

async def setup(bot):
    """Set up basic commands"""
    
    @bot.tree.command(name="info", description="Get information about the bot")
    async def info_command(interaction: discord.Interaction):
        """Show information about the bot"""
        embed = discord.Embed(
            title="Bishop Bot Information",
            description="Voice-activated assistant for tabletop RPGs",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Bot Information",
            value=f"Connected to {len(bot.guilds)} servers\n"
                  f"Uptime: {bot.get_uptime()}",
            inline=False
        )
        
        embed.set_footer(text="Created by Bioku87")
        
        await interaction.response.send_message(embed=embed)
    
    logger.info("Basic commands registered")