"""
Bishop Bot - Rules Commands
Last updated: 2025-05-31 19:08:32 UTC by Bioku87
"""
import discord
import logging
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('bishop_bot.commands.rules')

async def register_rules_commands(bot):
    """Register rules-related commands"""
    
    # Default systems for autocomplete
    AVAILABLE_SYSTEMS = ["dnd5e", "pathfinder2e", "callofcthulhu"]
    
    # System autocomplete
    async def system_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        systems = AVAILABLE_SYSTEMS
        
        # Get actual systems from rules manager if available
        if hasattr(bot, 'rules_manager'):
            try:
                systems = bot.rules_manager.get_available_systems()
            except:
                pass
        
        # Filter by current input
        filtered = [s for s in systems if current.lower() in s.lower()]
        
        # Convert to choices
        return [app_commands.Choice(name=s, value=s) for s in filtered[:25]]
    
    @bot.tree.command(name="lookup", description="Look up a game rule")
    @app_commands.describe(
        system="Game system (e.g., dnd5e, pathfinder2e)",
        query="Rule to look up"
    )
    @app_commands.autocomplete(system=system_autocomplete)
    async def lookup_command(interaction: discord.Interaction, system: str, query: str):
        try:
            # Check if rules manager exists
            if not hasattr(bot, 'rules_manager'):
                await interaction.response.send_message("Rules lookup is not available.", ephemeral=True)
                return
            
            # Search for rules
            results = bot.rules_manager.search_rules(system, query)
            
            if not results:
                await interaction.response.send_message(f"No rules found for '{query}' in {system}.", ephemeral=True)
                return
            
            # Create embed response
            embed = discord.Embed(
                title=f"Rule Lookup: {query}",
                description=f"Found {len(results)} rule(s) in {system}",
                color=discord.Color.green()
            )
            
            # Add rules to embed (limit to first 5)
            for i, rule in enumerate(results[:5]):
                embed.add_field(
                    name=f"{rule.get('name', 'Unknown')} ({rule.get('category', 'General')})",
                    value=rule.get('description', 'No description available')[:1024],  # Discord limit
                    inline=False
                )
            
            # Add note if more results were found
            if len(results) > 5:
                embed.set_footer(text=f"Showing 5 of {len(results)} results. Refine your search for more specific results.")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in lookup command: {e}")
            await interaction.response.send_message("An error occurred during rule lookup.", ephemeral=True)
    
    @bot.tree.command(name="condition", description="Look up a game condition")
    @app_commands.describe(
        system="Game system (e.g., dnd5e, pathfinder2e)",
        condition="Condition to look up"
    )
    @app_commands.autocomplete(system=system_autocomplete)
    async def condition_command(interaction: discord.Interaction, system: str, condition: str):
        try:
            # Check if rules manager exists
            if not hasattr(bot, 'rules_manager'):
                await interaction.response.send_message("Condition lookup is not available.", ephemeral=True)
                return
            
            # Look up the condition
            rule = bot.rules_manager.get_rule(system, "conditions", condition.lower())
            
            if not rule:
                await interaction.response.send_message(f"Condition '{condition}' not found in {system}.", ephemeral=True)
                return
            
            # Create embed response
            embed = discord.Embed(
                title=rule.get('name', 'Unknown Condition'),
                description=rule.get('description', 'No description available'),
                color=discord.Color.red()
            )
            
            # Add additional fields if they exist
            for key, value in rule.items():
                if key not in ['name', 'description'] and isinstance(value, str):
                    embed.add_field(
                        name=key.title(),
                        value=value,
                        inline=True
                    )
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in condition command: {e}")
            await interaction.response.send_message("An error occurred during condition lookup.", ephemeral=True)
    
    @bot.tree.command(name="spell", description="Look up a spell")
    @app_commands.describe(
        system="Game system (e.g., dnd5e, pathfinder2e)",
        spell="Spell to look up"
    )
    @app_commands.autocomplete(system=system_autocomplete)
    async def spell_command(interaction: discord.Interaction, system: str, spell: str):
        try:
            # Check if rules manager exists
            if not hasattr(bot, 'rules_manager'):
                await interaction.response.send_message("Spell lookup is not available.", ephemeral=True)
                return
            
            # Since we don't have spell data yet, just show a placeholder
            await interaction.response.send_message(
                f"Spell lookup for '{spell}' in {system} not yet implemented.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in spell command: {e}")
            await interaction.response.send_message("An error occurred during spell lookup.", ephemeral=True)
    
    logger.info("Rules commands registered")
    return True