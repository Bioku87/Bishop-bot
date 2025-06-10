"""
Bishop Bot - Admin Commands
Last updated: 2025-05-31 19:08:32 UTC by Bioku87
"""
import discord
import logging
import os
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('bishop_bot.commands.admin')

async def register_admin_commands(bot):
    """Register admin-related commands"""
    
    # Check admin permission
    def is_admin():
        def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)
    
    @bot.tree.command(name="setup", description="Set up the bot for this server")
    @is_admin()
    async def setup_command(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create server directory structure
            guild_id = interaction.guild.id
            
            # Create guild-specific directories
            directories = [
                f"data/audio/soundboard/{guild_id}",
                f"data/characters/{guild_id}",
                f"data/voice/sessions/{guild_id}"
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            # Create or load guild settings
            guild_settings = {}
            try:
                if hasattr(bot, 'db'):
                    result = bot.db.fetchone("SELECT settings FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
                    if result and 'settings' in result:
                        import json
                        guild_settings = json.loads(result['settings'])
                    else:
                        # Create default settings
                        guild_settings = {
                            "prefix": "/",
                            "welcome_channel": None,
                            "admin_role": None,
                            "voice_recognition_enabled": True,
                            "default_volume": 0.5
                        }
                        
                        # Save settings
                        bot.db.insert('guild_settings', {
                            'guild_id': str(guild_id),
                            'settings': json.dumps(guild_settings)
                        })
            except Exception as e:
                logger.error(f"Error loading guild settings: {e}")
            
            await interaction.followup.send(
                "Bishop Bot set up for this server. Use `/settings` to configure settings."
            )
        except Exception as e:
            logger.error(f"Error in setup command: {e}")
            await interaction.followup.send("An error occurred during setup.")
    
    @bot.tree.command(name="settings", description="Configure bot settings")
    @is_admin()
    async def settings_command(interaction: discord.Interaction):
        try:
            # Check if database exists
            if not hasattr(bot, 'db'):
                await interaction.response.send_message("Settings management is not available.", ephemeral=True)
                return
            
            # Get current settings
            guild_id = interaction.guild.id
            result = bot.db.fetchone("SELECT settings FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
            
            if not result:
                await interaction.response.send_message("Please run `/setup` first.", ephemeral=True)
                return
            
            # Parse settings
            import json
            settings = json.loads(result['settings'])
            
            # Create embed response
            embed = discord.Embed(
                title="Server Settings",
                description="Current settings for this server",
                color=discord.Color.blue()
            )
            
            for key, value in settings.items():
                embed.add_field(
                    name=key,
                    value=str(value),
                    inline=True
                )
            
            # Add instructions
            embed.add_field(
                name="How to Change Settings",
                value="Use `/setsetting key value` to change a setting",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await interaction.response.send_message("An error occurred while getting settings.", ephemeral=True)
    
    @bot.tree.command(name="setsetting", description="Change a bot setting")
    @app_commands.describe(
        key="Setting key",
        value="Setting value"
    )
    @is_admin()
    async def set_setting_command(interaction: discord.Interaction, key: str, value: str):
        try:
            # Check if database exists
            if not hasattr(bot, 'db'):
                await interaction.response.send_message("Settings management is not available.", ephemeral=True)
                return
            
            # Get current settings
            guild_id = interaction.guild.id
            result = bot.db.fetchone("SELECT settings FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
            
            if not result:
                await interaction.response.send_message("Please run `/setup` first.", ephemeral=True)
                return
            
            # Parse settings
            import json
            settings = json.loads(result['settings'])
            
            # Update setting
            settings[key] = value
            
            # Save settings
            bot.db.update('guild_settings', {
                'settings': json.dumps(settings),
                'updated_at': 'CURRENT_TIMESTAMP'
            }, 'guild_id = ?', (str(guild_id),))
            
            await interaction.response.send_message(f"Setting updated: {key} = {value}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in set_setting command: {e}")
            await interaction.response.send_message("An error occurred while updating the setting.", ephemeral=True)
    
    @bot.tree.command(name="backup", description="Backup bot data")
    @is_admin()
    async def backup_command(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create backup directory
            import datetime
            import shutil
            
            backup_dir = "data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup database
            if hasattr(bot, 'db') and hasattr(bot.db, 'db_path'):
                db_backup = f"{backup_dir}/bishop_db_{timestamp}.sqlite"
                shutil.copy2(bot.db.db_path, db_backup)
                
                await interaction.followup.send(f"Database backed up to {db_backup}")
            else:
                await interaction.followup.send("Database backup not available.")
        except Exception as e:
            logger.error(f"Error in backup command: {e}")
            await interaction.followup.send("An error occurred while creating a backup.")
    
    logger.info("Admin commands registered")
    return True