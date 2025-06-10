"""
Bishop Bot - Music Player
Last updated: 2025-05-31 15:23:46 UTC by Bioku87

This module manages music playback and playlist management.
"""
import os
import asyncio
import logging
import random
from typing import Dict, List, Optional, Union, Tuple

import discord
from discord.ext import commands
import yt_dlp

logger = logging.getLogger('bishop_bot.voice.music_player')

# YT-DLP configuration
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # Bind to IPv4
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

class MusicTrack:
    """Represents a music track for playback"""
    
    def __init__(self, url, title, duration, thumbnail, requester):
        self.url = url
        self.title = title
        self.duration = duration
        self.thumbnail = thumbnail
        self.requester = requester
        self.source = None
        
    @classmethod
    async def from_url(cls, url, requester, *, loop=None):
        """Create a track from a URL or search terms"""
        loop = loop or asyncio.get_event_loop()
        
        try:
            ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                # Take first item from a playlist
                data = data['entries'][0]
                
            # Create track
            return cls(
                url=data['url'],
                title=data['title'],
                duration=data.get('duration', 0),
                thumbnail=data.get('thumbnail', ''),
                requester=requester
            )
        except Exception as e:
            logger.error(f"Error creating track from URL '{url}': {e}")
            raise
    
    def create_source(self):
        """Create a Discord audio source for this track"""
        self.source = discord.FFmpegPCMAudio(self.url, **ffmpeg_options)
        return discord.PCMVolumeTransformer(self.source)
        
    def __str__(self):
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            duration = f"{hours}h {minutes}m {seconds}s"
        else:
            duration = f"{minutes}m {seconds}s"
            
        return f"**{self.title}** ({duration}) - requested by {self.requester}"

class GuildMusicState:
    """Manages music playback state for a specific guild"""
    
    def __init__(self, guild):
        self.guild = guild
        self.voice_client = None
        self.current_track = None
        self.queue = asyncio.Queue()
        self.next_track = asyncio.Event()
        self.volume = 0.5  # 50% volume
        self.player_task = None
        self.skip_votes = set()
        self.paused = False
        
    def is_playing(self):
        """Check if the player is currently playing"""
        return self.voice_client and self.voice_client.is_playing()
        
    def stop(self):
        """Stop playback and clear the queue"""
        self.queue = asyncio.Queue()
        
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.is_playing():
                self.voice_client.stop()
                
        self.current_track = None
        self.skip_votes.clear()
        
    def set_volume(self, volume):
        """Set playback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        
        if self.voice_client and self.voice_client.source:
            self.voice_client.source.volume = self.volume
            
    def toggle_pause(self):
        """Toggle pause state"""
        if not self.voice_client:
            return False
            
        if self.voice_client.is_paused():
            self.voice_client.resume()
            self.paused = False
            return False
        elif self.voice_client.is_playing():
            self.voice_client.pause()
            self.paused = True
            return True
        
        return self.paused
        
    def skip(self):
        """Skip the current track"""
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
                return True
        return False
        
    def add_skip_vote(self, user_id):
        """Add a vote to skip the current track"""
        self.skip_votes.add(user_id)
        
    def get_queue_info(self):
        """Get information about the queue"""
        return {
            "current": str(self.current_track) if self.current_track else None,
            "queue_size": self.queue.qsize(),
            "is_playing": self.is_playing(),
            "is_paused": self.paused
        }
        
    async def player_loop(self):
        """Main player loop"""
        await self.guild.me.edit(deafen=True)
        
        while True:
            self.next_track.clear()
            self.skip_votes.clear()
            
            # Wait for the next track
            try:
                self.current_track = await asyncio.wait_for(self.queue.get(), timeout=300)
            except asyncio.TimeoutError:
                # No track for 5 minutes, cleanup
                if self.player_task:
                    self.player_task.cancel()
                    self.player_task = None
                return self.cleanup()
                
            # Create source and play
            try:
                source = self.current_track.create_source()
                source.volume = self.volume
                
                self.voice_client.play(
                    source, 
                    after=lambda _: asyncio.run_coroutine_threadsafe(
                        self.next_track.set(), 
                        asyncio.get_event_loop()
                    )
                )
                
                # Wait until the song is done or skipped
                await self.next_track.wait()
                
            except Exception as e:
                logger.error(f"Error playing track: {e}")
                continue
                
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.voice_client:
                asyncio.create_task(self.voice_client.disconnect())
                self.voice_client = None
        except Exception as e:
            logger.error(f"Error in music player cleanup: {e}")


class MusicPlayer:
    """Manages music playback across multiple guilds"""
    
    def __init__(self):
        self.guild_states: Dict[int, GuildMusicState] = {}
        
    async def join_voice(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        """Join a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                return False, "You are not connected to a voice channel."
                
        # Get or create guild state
        if ctx.guild.id not in self.guild_states:
            self.guild_states[ctx.guild.id] = GuildMusicState(ctx.guild)
            
        guild_state = self.guild_states[ctx.guild.id]
        
        # Check if already connected
        if guild_state.voice_client and guild_state.voice_client.is_connected():
            await guild_state.voice_client.move_to(channel)
        else:
            try:
                guild_state.voice_client = await channel.connect()
            except discord.ClientException as e:
                logger.error(f"Error connecting to voice: {e}")
                return False, f"Error connecting to voice: {e}"
                
        return True, f"Connected to {channel.name}"
        
    async def leave_voice(self, ctx: commands.Context):
        """Leave the voice channel"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not connected to any voice channel."
            
        guild_state = self.guild_states[ctx.guild.id]
        
        # Stop playback and clear queue
        guild_state.stop()
        
        # Disconnect
        if guild_state.voice_client and guild_state.voice_client.is_connected():
            await guild_state.voice_client.disconnect()
            del self.guild_states[ctx.guild.id]
            return True, "Disconnected from voice channel."
        
        return False, "Not connected to any voice channel."
        
    async def play(self, ctx: commands.Context, url: str):
        """Play a track from URL or search terms"""
        if ctx.guild.id not in self.guild_states:
            success, message = await self.join_voice(ctx)
            if not success:
                return False, message
                
        guild_state = self.guild_states[ctx.guild.id]
        
        # Check voice client
        if not guild_state.voice_client or not guild_state.voice_client.is_connected():
            success, message = await self.join_voice(ctx)
            if not success:
                return False, message
                
        try:
            # Create track
            track = await MusicTrack.from_url(url, ctx.author.display_name)
            
            # Add to queue
            await guild_state.queue.put(track)
            
            # Start player task if needed
            if not guild_state.player_task or guild_state.player_task.done():
                guild_state.player_task = asyncio.create_task(guild_state.player_loop())
                
            return True, f"Added to queue: {track.title}"
            
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            return False, f"Error playing track: {e}"
            
    def skip(self, ctx: commands.Context):
        """Skip the current track"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        
        if not guild_state.current_track:
            return False, "Not playing anything."
            
        # Skip the track
        if guild_state.skip():
            return True, "Skipped the current track."
        else:
            return False, "Not currently playing."
            
    def pause(self, ctx: commands.Context):
        """Pause playback"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        
        if guild_state.toggle_pause():
            return True, "Paused the music."
        else:
            return False, "Already paused or not playing."
            
    def resume(self, ctx: commands.Context):
        """Resume playback"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        
        if not guild_state.toggle_pause():
            return True, "Resumed the music."
        else:
            return False, "Not paused or not playing."
            
    def set_volume(self, ctx: commands.Context, volume: float):
        """Set volume (0-100)"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        
        # Convert to 0.0-1.0 range
        normalized_volume = max(0.0, min(1.0, volume / 100.0))
        guild_state.set_volume(normalized_volume)
        
        return True, f"Volume set to {int(volume)}%"
        
    def get_queue(self, ctx: commands.Context):
        """Get the current queue"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        queue_info = guild_state.get_queue_info()
        
        return True, queue_info
        
    def stop(self, ctx: commands.Context):
        """Stop playback and clear the queue"""
        if ctx.guild.id not in self.guild_states:
            return False, "Not playing anything."
            
        guild_state = self.guild_states[ctx.guild.id]
        guild_state.stop()
        
        return True, "Stopped playback and cleared the queue."
        
    def cleanup(self):
        """Clean up resources for all guilds"""
        for guild_id, state in list(self.guild_states.items()):
            state.cleanup()
            
        self.guild_states.clear()

# Create singleton instance
music_player = MusicPlayer()