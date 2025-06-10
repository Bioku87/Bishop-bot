"""
Bishop Bot - Dice Commands
Last updated: 2025-05-31 18:33:27 UTC by Bioku87
"""
import discord
import logging
import random
from discord import app_commands
from discord.ext import commands
from game.dice import DiceManager

logger = logging.getLogger('bishop_bot.commands.dice')

async def register_dice_commands(bot):
    """Register dice-related commands"""
    
    # Initialize dice manager if not exists
    if not hasattr(bot, 'dice_manager'):
        bot.dice_manager = DiceManager()
    
    @bot.tree.command(name="roll", description="Roll dice (e.g. 2d6+3, 1d20)")
    @app_commands.describe(dice="Dice expression (e.g. 2d6+3, 1d20)")
    async def roll_command(interaction: discord.Interaction, dice: str):
        try:
            # Roll the dice
            result = bot.dice_manager.roll_with_context(dice)
            
            # Create embed response
            embed = discord.Embed(
                title="Dice Roll",
                description=f"Rolling: `{result.expression}`",
                color=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
            
            # Add detailed breakdown
            embed.add_field(
                name="Result",
                value=f"**{result.total}**",
                inline=True
            )
            
            # Add individual dice results
            dice_results = ", ".join(str(r) for r in result.rolls)
            embed.add_field(
                name="Dice",
                value=f"[{dice_results}]",
                inline=True
            )
            
            # Add breakdown calculation
            embed.add_field(
                name="Breakdown",
                value=result.breakdown,
                inline=False
            )
            
            # Set footer with user
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
        except ValueError as ve:
            await interaction.response.send_message(f"Error: {str(ve)}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in roll command: {e}")
            await interaction.response.send_message("An error occurred while rolling the dice.", ephemeral=True)
    
    @bot.tree.command(name="advantage", description="Roll with advantage (2d20, take highest)")
    @app_commands.describe(modifier="Modifier to add (e.g. +3, -2)")
    async def advantage_command(interaction: discord.Interaction, modifier: str = "0"):
        try:
            # Clean modifier input
            mod = modifier.strip()
            if mod and not mod.startswith('+') and not mod.startswith('-'):
                mod = '+' + mod
            
            # Roll the dice
            result = bot.dice_manager.roll_advanced(f"1d20a{mod}")
            
            # Create embed response
            embed = discord.Embed(
                title="Advantage Roll",
                description=f"Rolling with advantage: `1d20{mod}`",
                color=discord.Color.green()
            )
            
            # Add result
            embed.add_field(
                name="Result",
                value=f"**{result.total}**",
                inline=True
            )
            
            # Add breakdown
            embed.add_field(
                name="Breakdown",
                value=result.breakdown,
                inline=False
            )
            
            # Set footer with user
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in advantage command: {e}")
            await interaction.response.send_message("An error occurred while rolling with advantage.", ephemeral=True)
    
    @bot.tree.command(name="disadvantage", description="Roll with disadvantage (2d20, take lowest)")
    @app_commands.describe(modifier="Modifier to add (e.g. +3, -2)")
    async def disadvantage_command(interaction: discord.Interaction, modifier: str = "0"):
        try:
            # Clean modifier input
            mod = modifier.strip()
            if mod and not mod.startswith('+') and not mod.startswith('-'):
                mod = '+' + mod
            
            # Roll the dice
            result = bot.dice_manager.roll_advanced(f"1d20d{mod}")
            
            # Create embed response
            embed = discord.Embed(
                title="Disadvantage Roll",
                description=f"Rolling with disadvantage: `1d20{mod}`",
                color=discord.Color.red()
            )
            
            # Add result
            embed.add_field(
                name="Result",
                value=f"**{result.total}**",
                inline=True
            )
            
            # Add breakdown
            embed.add_field(
                name="Breakdown",
                value=result.breakdown,
                inline=False
            )
            
            # Set footer with user
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in disadvantage command: {e}")
            await interaction.response.send_message("An error occurred while rolling with disadvantage.", ephemeral=True)
    
    @bot.tree.command(name="abilitycheck", description="Roll an ability check")
    @app_commands.choices(ability=[
        app_commands.Choice(name="Strength", value="strength"),
        app_commands.Choice(name="Dexterity", value="dexterity"),
        app_commands.Choice(name="Constitution", value="constitution"),
        app_commands.Choice(name="Intelligence", value="intelligence"),
        app_commands.Choice(name="Wisdom", value="wisdom"),
        app_commands.Choice(name="Charisma", value="charisma")
    ])
    @app_commands.describe(
        ability="The ability to check",
        modifier="Additional modifier (optional)",
        advantage="Roll with advantage",
        disadvantage="Roll with disadvantage"
    )
    async def ability_check_command(
        interaction: discord.Interaction,
        ability: app_commands.Choice[str],
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False
    ):
        try:
            # Determine the roll type
            roll_type = ""
            if advantage and not disadvantage:
                roll_type = "a"  # Advantage
            elif disadvantage and not advantage:
                roll_type = "d"  # Disadvantage
            
            # Construct the dice expression
            dice_expr = f"1d20{roll_type}"
            if modifier != 0:
                dice_expr += f"{'+' if modifier > 0 else ''}{modifier}"
            
            # Roll the dice
            result = bot.dice_manager.roll_with_context(dice_expr)
            
            # Create embed response
            embed = discord.Embed(
                title=f"{ability.name} Check",
                description=f"Rolling {ability.name.lower()} check: `{dice_expr}`",
                color=discord.Color.gold()
            )
            
            # Add result
            embed.add_field(
                name="Result",
                value=f"**{result.total}**",
                inline=True
            )
            
            # Add roll details
            embed.add_field(
                name="Roll",
                value=f"{result.rolls[0]}{'+' + str(modifier) if modifier > 0 else ('' if modifier == 0 else str(modifier))}",
                inline=True
            )
            
            # Add roll type
            if advantage:
                embed.add_field(name="Roll Type", value="Advantage", inline=True)
            elif disadvantage:
                embed.add_field(name="Roll Type", value="Disadvantage", inline=True)
            else:
                embed.add_field(name="Roll Type", value="Normal", inline=True)
            
            # Set footer with user
            embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in ability check command: {e}")
            await interaction.response.send_message("An error occurred while rolling the ability check.", ephemeral=True)
    
    logger.info("Dice commands registered")
    return True