"""
Bishop Bot - Audio Commands (Simplified)
Last updated: 2025-05-31 23:13:05 UTC by Bioku87
"""
import discord
import logging
import os
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger('bishop_bot.commands.audio')

async def register_audio_commands(bot):
    """Register audio-related commands"""
    
    @bot.tree.command(name="play", description="Play a sound from the soundboard")
    @app_commands.describe(
        sound="Sound name",
        category="Sound category (Default, Combat, Ambience)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Default", value="Default"),
        app_commands.Choice(name="Combat", value="Combat"),
        app_commands.Choice(name="Ambience", value="Ambience")
    ])
    async def play_command(
        interaction: discord.Interaction, 
        sound: str, 
        category: app_commands.Choice[str] = None
    ):
        try:
            # Check if audio manager exists
            if not hasattr(bot, 'audio_manager'):
                await interaction.response.send_message("Audio management is not available.", ephemeral=True)
                return
            
            # Check if bot is in a voice channel
            if not bot.audio_manager.is_connected(interaction.guild_id):
                # Check if the user is in a voice channel
                if interaction.user.voice and interaction.user.voice.channel:
                    # Join the voice channel
                    await interaction.response.defer(ephemeral=True)
                    success = await bot.audio_manager.join_voice_channel(interaction.user.voice.channel)
                    
                    if not success:
                        await interaction.followup.send("Failed to join voice channel.", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message("You need to be in a voice channel first!", ephemeral=True)
                    return
            
            # Use Default category if none specified
            category_name = category.value if category else "Default"
            
            # Play the sound
            await interaction.response.defer(ephemeral=False)
            success = await bot.audio_manager.play_sound(interaction.guild_id, sound, category_name)
            
            if success:
                await interaction.followup.send(f"🔊 Playing sound: **{sound}** from category *{category_name}*")
            else:
                await interaction.followup.send(f"Sound not found: {sound} in category {category_name}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await interaction.followup.send("An error occurred while playing the sound.", ephemeral=True)
    
    @bot.tree.command(name="stop", description="Stop audio playback")
    async def stop_command(interaction: discord.Interaction):
        try:
            # Check if audio manager exists
            if not hasattr(bot, 'audio_manager'):
                await interaction.response.send_message("Audio management is not available.", ephemeral=True)
                return
            
            # Check if bot is in a voice channel
            if not bot.audio_manager.is_connected(interaction.guild_id):
                await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
                return
            
            # Stop playback
            success = bot.audio_manager.stop_playback(interaction.guild_id)
            
            if success:
                await interaction.response.send_message("⏹️ Stopped audio playback.")
            else:
                await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in stop command: {e}")
            await interaction.response.send_message("An error occurred while stopping playback.", ephemeral=True)
    
    @bot.tree.command(name="soundboard", description="Show available sounds")
    @app_commands.describe(category="Sound category (Default, Combat, Ambience)")
    @app_commands.choices(category=[
        app_commands.Choice(name="Default", value="Default"),
        app_commands.Choice(name="Combat", value="Combat"),
        app_commands.Choice(name="Ambience", value="Ambience")
    ])
    async def soundboard_command(
        interaction: discord.Interaction,
        category: app_commands.Choice[str] = None
    ):
        try:
            # Check if audio manager exists
            if not hasattr(bot, 'audio_manager'):
                await interaction.response.send_message("Audio management is not available.", ephemeral=True)
                return
            
            # Use Default category if none specified
            category_name = category.value if category else "Default"
            
            # Get sounds in category
            sounds = bot.audio_manager.get_sounds_in_category(category_name)
            
            if not sounds:
                await interaction.response.send_message(f"No sounds found in category {category_name}.", ephemeral=True)
                return
            
            # Create embed response
            embed = discord.Embed(
                title=f"Soundboard - {category_name}",
                description=f"Available sounds in category {category_name}",
                color=discord.Color.purple()
            )
            
            # List all sounds alphabetically
            sound_names = [sound.name for sound in sounds]
            sound_names.sort()
            
            # Split into groups of ~15 sounds per field to avoid Discord limits
            groups = []
            while sound_names:
                groups.append(sound_names[:15])
                sound_names = sound_names[15:]
            
            if groups:
                for i, group in enumerate(groups):
                    sound_list = ", ".join([f"`{name}`" for name in group])
                    embed.add_field(
                        name=f"Sounds {i+1}" if len(groups) > 1 else "Sounds",
                        value=sound_list,
                        inline=False
                    )
            else:
                embed.add_field(name="No sounds found", value="This category is empty.")
            
            embed.set_footer(text="Use /play <sound> to play a sound")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error in soundboard command: {e}")
            await interaction.response.send_message("An error occurred while getting sounds.", ephemeral=True)
    
    logger.info("Audio commands registered")
    return True