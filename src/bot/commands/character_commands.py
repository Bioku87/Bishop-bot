"""
Bishop Bot - Character Commands
Last updated: 2025-05-31 19:08:32 UTC by Bioku87
"""
import discord
import logging
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('bishop_bot.commands.characters')

async def register_character_commands(bot):
    """Register character-related commands"""
    
    @bot.tree.command(name="createchar", description="Create a new character")
    @app_commands.describe(
        name="Character name",
        character_class="Character class (e.g., Fighter, Wizard)",
        race="Character race (e.g., Human, Elf)",
        level="Character level"
    )
    async def create_char_command(
        interaction: discord.Interaction, 
        name: str, 
        character_class: str, 
        race: str, 
        level: int = 1
    ):
        try:
            # Check if character manager exists
            if not hasattr(bot, 'character_manager'):
                await interaction.response.send_message("Character management is not available.", ephemeral=True)
                return
            
            # Create character
            character = bot.character_manager.create_character(
                player_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id),
                name=name,
                character_class=character_class,
                race=race,
                level=level
            )
            
            if character:
                # Create embed response
                embed = character.to_embed()
                embed.set_footer(text=f"Created by {interaction.user.display_name}")
                
                await interaction.response.send_message(
                    content=f"Character '{name}' created successfully!",
                    embed=embed
                )
            else:
                await interaction.response.send_message("Failed to create character.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in create_char command: {e}")
            await interaction.response.send_message("An error occurred while creating the character.", ephemeral=True)
    
    @bot.tree.command(name="listchars", description="List your characters")
    async def list_chars_command(interaction: discord.Interaction):
        try:
            # Check if character manager exists
            if not hasattr(bot, 'character_manager'):
                await interaction.response.send_message("Character management is not available.", ephemeral=True)
                return
            
            # Get player's characters
            characters = bot.character_manager.get_player_characters(
                player_id=str(interaction.user.id),
                guild_id=str(interaction.guild_id)
            )
            
            if not characters:
                await interaction.response.send_message("You don't have any characters in this server.", ephemeral=True)
                return
            
            # Create embed response
            embed = discord.Embed(
                title="Your Characters",
                description=f"You have {len(characters)} character(s) in this server.",
                color=discord.Color.blue()
            )
            
            for character in characters:
                embed.add_field(
                    name=f"{character.name} (ID: {character.id})",
                    value=f"Level {character.level} {character.race} {character.character_class}",
                    inline=False
                )
            
            embed.set_footer(text=f"Use /viewchar <id> to view details")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in list_chars command: {e}")
            await interaction.response.send_message("An error occurred while listing your characters.", ephemeral=True)
    
    @bot.tree.command(name="viewchar", description="View character details")
    @app_commands.describe(character_id="Character ID from /listchars")
    async def view_char_command(interaction: discord.Interaction, character_id: int):
        try:
            # Check if character manager exists
            if not hasattr(bot, 'character_manager'):
                await interaction.response.send_message("Character management is not available.", ephemeral=True)
                return
            
            # Get character
            character = bot.character_manager.get_character(character_id)
            
            if not character:
                await interaction.response.send_message("Character not found.", ephemeral=True)
                return
            
            # Check if user owns the character or is an admin
            is_owner = str(interaction.user.id) == character.player_id
            is_admin = interaction.user.guild_permissions.administrator
            
            if not is_owner and not is_admin:
                await interaction.response.send_message("You don't have permission to view this character.", ephemeral=True)
                return
            
            # Create embed response
            embed = character.to_embed()
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in view_char command: {e}")
            await interaction.response.send_message("An error occurred while viewing the character.", ephemeral=True)
    
    logger.info("Character commands registered")
    return True