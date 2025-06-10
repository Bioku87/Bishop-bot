"""
Bishop Bot - Commands Initialization
Last updated: 2025-05-31 23:32:22 UTC by Bioku87
"""
import os
import logging
import discord
from discord import app_commands

logger = logging.getLogger('bishop_bot.commands')

async def register_commands(bot):
    """Register all bot commands"""
    if not bot:
        logger.error("Cannot register commands: bot is None")
        return False
        
    logger.info("Registering bot commands...")
    
    # Basic ping command
    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping_command(interaction: discord.Interaction):
        try:
            await interaction.response.send_message(f"Pong! Bot latency: {round(bot.latency * 1000)}ms")
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
    
    # Basic info command
    @bot.tree.command(name="info", description="Get information about the bot")
    async def info_command(interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="Bishop Bot Information",
                description="Voice channel recording and soundboard bot",
                color=discord.Color.blue()
            )
            
            uptime = "Unknown"
            try:
                uptime = bot.get_uptime()
            except Exception as e:
                logger.error(f"Error getting uptime: {e}")
                
            embed.add_field(
                name="Bot Stats",
                value=f"Servers: {len(bot.guilds)}\n"
                      f"Uptime: {uptime}",
                inline=False
            )
            
            # Add component status information
            if hasattr(bot, 'initialized_components'):
                status_list = []
                for component, status in bot.initialized_components.items():
                    emoji = "✅" if status else "❌"
                    status_list.append(f"{emoji} {component.title()}")
                
                if status_list:
                    embed.add_field(
                        name="Components",
                        value="\n".join(status_list),
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in info command: {e}")
    
    # Basic help command
    @bot.tree.command(name="help", description="Show available commands")
    async def help_command(interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="Bishop Bot Help",
                description="Available commands:",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="General",
                value="`/ping` - Check bot latency\n"
                      "`/info` - View bot information\n"
                      "`/help` - Show this help message",
                inline=False
            )
            
            embed.add_field(
                name="Voice",
                value="`/join` - Join a voice channel\n"
                      "`/leave` - Leave the voice channel\n"
                      "`/record` - Start recording the voice channel\n"
                      "`/stoprecord` - Stop recording",
                inline=False
            )
            
            embed.add_field(
                name="Audio",
                value="`/play` - Play a sound\n"
                      "`/stop` - Stop playback\n"
                      "`/soundboard` - Show available sounds",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in help command: {e}")
    
    # Sync commands with Discord
    try:
        logger.info("Syncing commands with Discord...")
        # For production: sync globally
        await bot.tree.sync()
        logger.info("Command sync complete!")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")
        return False
    
    return True