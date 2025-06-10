"""
Bishop Bot - Control Window
Last updated: 2025-06-01 05:44:18 UTC by Bioku87
"""
import threading
import logging
import os
import platform
import time
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import asyncio
import json
import shutil
import sqlite3
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger('bishop_bot.control_window')

class ControlWindow:
    """Main control window for Bishop Bot"""
    
    def __init__(self, bot):
        """Initialize the control window"""
        self.bot = bot
        self.running = True
        self.root = None
        self.server_frames = {}  # Store server frames for updates
        self.sound_buttons = {}  # Store sound buttons
        self.audio_groups = {}   # Store audio groups
        
        # Print debug info
        logger.info(f"Initializing control window for bot: {bot}")
        
        # Start in a separate thread to not block the bot
        logger.info("Starting control window thread")
        self.thread = threading.Thread(target=self._run_window)
        self.thread.daemon = True
        self.thread.start()
    
    def _run_window(self):
        """Run the control window in its own thread"""
        try:
            # Create the main window
            self.root = tk.Tk()
            self.root.title("Bishop Bot Control")
            self.root.geometry("800x600")
            self.root.minsize(600, 400)
            
            # Set theme based on OS - with better error handling
            try:
                if platform.system() == "Windows":
                    theme_path = os.path.join(os.path.dirname(__file__), 'sun-valley.tcl')
                    if os.path.exists(theme_path):
                        self.root.tk.call('source', theme_path)
                        try:
                            # Try to set theme, but don't fail if it doesn't work
                            self.root.tk.call('set_theme', 'dark')
                            logger.info("Theme loaded successfully")
                        except Exception as theme_cmd_error:
                            logger.warning(f"Theme command error: {theme_cmd_error}")
                            # Try using the theme directly
                            try:
                                ttk.Style().theme_use('sunvalley')
                                logger.info("Theme applied directly")
                            except:
                                logger.warning("Could not apply theme, using default")
                    else:
                        logger.warning(f"Theme file not found: {theme_path}")
            except Exception as theme_error:
                logger.error(f"Error setting theme: {theme_error}")
            
            # Configure grid layout
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=0)  # Status frame
            self.root.rowconfigure(1, weight=1)  # Tab control
            self.root.rowconfigure(2, weight=0)  # Bottom buttons
            
            # Set up status frame
            self._setup_status_frame()
            
            # Set up tab control
            self._setup_tab_control()
            
            # Set up bottom buttons (without settings button)
            self._setup_buttons()
            
            # Bind closing event
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Update status every second
            self._update_status()
            
            # Start the main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Error creating control window: {e}")
            try:
                messagebox.showerror("Error", f"Failed to create control window: {e}")
            except:
                pass
            self.running = False
    
    def _setup_status_frame(self):
        """Set up the status frame"""
        status_frame = ttk.LabelFrame(self.root, text="Bot Status")
        status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Configure grid layout for status frame
        status_frame.columnconfigure(0, weight=0)
        status_frame.columnconfigure(1, weight=1)
        
        # Status indicators
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.connection_status = ttk.Label(status_frame, text="Connected")
        self.connection_status.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(status_frame, text="Servers:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.servers_status = ttk.Label(status_frame, text="0")
        self.servers_status.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(status_frame, text="Uptime:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.uptime_status = ttk.Label(status_frame, text="00:00:00")
        self.uptime_status.grid(row=2, column=1, padx=5, pady=2, sticky="w")
    
    def _setup_tab_control(self):
        """Set up the tab control"""
        tab_control = ttk.Notebook(self.root)
        tab_control.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Servers tab
        servers_tab = ttk.Frame(tab_control)
        tab_control.add(servers_tab, text="Servers")
        self._setup_servers_tab(servers_tab)
        
        # Voice tab
        voice_tab = ttk.Frame(tab_control)
        tab_control.add(voice_tab, text="Voice")
        self._setup_voice_tab(voice_tab)
        
        # Audio tab
        audio_tab = ttk.Frame(tab_control)
        tab_control.add(audio_tab, text="Audio")
        self._setup_audio_tab(audio_tab)
        
        # Soundboard tab
        soundboard_tab = ttk.Frame(tab_control)
        tab_control.add(soundboard_tab, text="Soundboard")
        self._setup_soundboard_tab(soundboard_tab)
        
        # Menu tab (NEW)
        menu_tab = ttk.Frame(tab_control)
        tab_control.add(menu_tab, text="Menu")
        self._setup_menu_tab(menu_tab)
        
        # Settings tab
        settings_tab = ttk.Frame(tab_control)
        tab_control.add(settings_tab, text="Settings")
        self._setup_settings_tab(settings_tab)
        
        # Logs tab
        logs_tab = ttk.Frame(tab_control)
        tab_control.add(logs_tab, text="Logs")
        self._setup_logs_tab(logs_tab)
    
    def _setup_servers_tab(self, parent):
        """Set up the servers tab showing connected servers"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Header
        parent.rowconfigure(1, weight=1)  # Server list
        
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        ttk.Label(header_frame, text="Connected Servers", font=("TkDefaultFont", 12, "bold")).pack(side="left", padx=5)
        ttk.Button(header_frame, text="Refresh", command=self._refresh_servers).pack(side="right", padx=5)
        
        # Server list in a scrollable frame
        server_canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=server_canvas.yview)
        server_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.grid(row=1, column=1, sticky="ns")
        server_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)
        
        server_frame = ttk.Frame(server_canvas)
        server_canvas.create_window((0, 0), window=server_frame, anchor="nw")
        
        # Store for updates
        self.server_list_frame = server_frame
        self.server_canvas = server_canvas
        
        # Configure scrolling
        server_frame.bind("<Configure>", lambda e: server_canvas.configure(scrollregion=server_canvas.bbox("all")))
        server_canvas.bind("<Configure>", lambda e: server_canvas.itemconfig(1, width=e.width))
        
        # Initial server population
        self._refresh_servers()
    
    def _refresh_servers(self):
        """Refresh the list of connected servers"""
        # Clear existing server frames
        for widget in self.server_list_frame.winfo_children():
            widget.destroy()
        self.server_frames = {}
        
        # Add servers
        if self.bot and hasattr(self.bot, 'guilds'):
            for i, guild in enumerate(self.bot.guilds):
                # Create frame
                server_frame = ttk.LabelFrame(self.server_list_frame, text=f"{guild.name}")
                server_frame.pack(fill="x", padx=5, pady=5)
                
                # Configure grid
                server_frame.columnconfigure(0, weight=1)  # Info column
                server_frame.columnconfigure(1, weight=0)  # Buttons column
                
                # Info frame (left side)
                info_frame = ttk.Frame(server_frame)
                info_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
                
                # Server info
                ttk.Label(info_frame, text=f"ID: {guild.id}").grid(row=0, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(info_frame, text=f"Members: {len(guild.members)}").grid(row=0, column=1, sticky="w", padx=5, pady=2)
                
                # Voice connection info
                voice_status = "Not connected"
                recording_status = "Not recording"
                
                # Safely check if is_connected exists and works
                if (hasattr(self.bot, 'voice_manager') and self.bot.voice_manager and 
                    hasattr(self.bot.voice_manager, 'is_connected')):
                    try:
                        voice_manager = self.bot.voice_manager
                        if voice_manager.is_connected(guild.id):
                            voice_status = "Connected"
                            # Safely check if is_recording exists
                            if hasattr(voice_manager, 'is_recording') and voice_manager.is_recording(guild.id):
                                recording_status = "Recording"
                    except:
                        # If there's any error, just use the defaults
                        pass
                
                ttk.Label(info_frame, text=f"Voice: {voice_status}").grid(row=1, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(info_frame, text=f"Recording: {recording_status}").grid(row=1, column=1, sticky="w", padx=5, pady=2)
                
                # Button frame (right side)
                button_frame = ttk.Frame(server_frame)
                button_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
                
                # Add disconnect/reconnect buttons
                is_connected = voice_status == "Connected"
                
                if is_connected:
                    ttk.Button(
                        button_frame, 
                        text="Disconnect", 
                        command=lambda g=guild: self._disconnect_from_server(g)
                    ).pack(side="top", padx=5, pady=2)
                else:
                    ttk.Button(
                        button_frame, 
                        text="Connect", 
                        command=lambda g=guild: self._connect_to_server(g)
                    ).pack(side="top", padx=5, pady=2)
                
                # Store frame for updates
                self.server_frames[guild.id] = server_frame
        else:
            # No servers
            ttk.Label(self.server_list_frame, text="Not connected to any servers").pack(padx=5, pady=10)
    
    def _disconnect_from_server(self, guild):
        """Disconnect from a server's voice channel"""
        try:
            if not hasattr(self.bot, 'voice_manager') or not self.bot.voice_manager:
                messagebox.showwarning("Not Available", "Voice manager is not available")
                return
            
            voice_manager = self.bot.voice_manager
            
            if not hasattr(voice_manager, 'disconnect_from_guild'):
                messagebox.showwarning("Not Available", "Voice manager doesn't support this operation")
                return
            
            # Check if bot has event loop
            if not hasattr(self.bot, 'loop'):
                messagebox.showwarning("Not Available", "Bot event loop not accessible")
                return
            
            # Run the disconnect coroutine
            try:
                asyncio.run_coroutine_threadsafe(
                    voice_manager.disconnect_from_guild(guild.id),
                    self.bot.loop
                )
                messagebox.showinfo("Disconnected", f"Disconnected from {guild.name}")
                
                # Refresh the server list
                self._refresh_servers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disconnect: {str(e)}")
                logger.error(f"Error disconnecting from {guild.name}: {e}")
        except Exception as e:
            logger.error(f"Error in disconnect_from_server: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def _connect_to_server(self, guild):
        """Connect to a server's voice channel"""
        try:
            if not hasattr(self.bot, 'voice_manager') or not self.bot.voice_manager:
                messagebox.showwarning("Not Available", "Voice manager is not available")
                return
            
            # Select a voice channel from the guild
            channel_selection = tk.Toplevel(self.root)
            channel_selection.title(f"Select Voice Channel - {guild.name}")
            channel_selection.geometry("400x300")
            
            ttk.Label(channel_selection, text=f"Select a voice channel in {guild.name}:").pack(padx=10, pady=10)
            
            # Get voice channels
            if not hasattr(guild, 'channels'):
                messagebox.showwarning("Not Available", "Cannot access guild channels")
                channel_selection.destroy()
                return
            
            # Filter voice channels
            voice_channels = [
                channel for channel in guild.channels 
                if hasattr(channel, 'type') and str(channel.type) == 'voice'
            ]
            
            if not voice_channels:
                ttk.Label(channel_selection, text="No voice channels found in this server.").pack(padx=10, pady=10)
                ttk.Button(channel_selection, text="Close", command=channel_selection.destroy).pack(pady=10)
                return
            
            # Create a listbox with voice channels
            frame = ttk.Frame(channel_selection)
            frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            listbox = tk.Listbox(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side="right", fill="y")
            listbox.pack(side="left", fill="both", expand=True)
            
            # Add channels to listbox
            for channel in voice_channels:
                listbox.insert(tk.END, channel.name)
            
            def join_selected_channel():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a voice channel", parent=channel_selection)
                    return
                
                channel = voice_channels[selection[0]]
                
                # Check if bot has event loop
                if not hasattr(self.bot, 'loop') or not hasattr(self.bot.voice_manager, 'join_voice_channel'):
                    messagebox.showwarning("Not Available", "Voice connection not available", parent=channel_selection)
                    channel_selection.destroy()
                    return
                
                # Run the join coroutine
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.bot.voice_manager.join_voice_channel(channel),
                        self.bot.loop
                    )
                    messagebox.showinfo("Connected", f"Connected to {channel.name}")
                    channel_selection.destroy()
                    
                    # Refresh the server list
                    self._refresh_servers()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to connect: {str(e)}", parent=channel_selection)
                    logger.error(f"Error connecting to {channel.name}: {e}")
            
            # Add buttons
            button_frame = ttk.Frame(channel_selection)
            button_frame.pack(pady=10, fill="x")
            
            ttk.Button(button_frame, text="Join Channel", command=join_selected_channel).pack(side="left", padx=10)
            ttk.Button(button_frame, text="Cancel", command=channel_selection.destroy).pack(side="right", padx=10)
            
        except Exception as e:
            logger.error(f"Error in connect_to_server: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def _setup_voice_tab(self, parent):
        """Set up the voice tab"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Controls
        parent.rowconfigure(1, weight=1)  # Status
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Button(control_frame, text="Start Recording", command=self._start_recording).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Stop Recording", command=self._stop_recording).pack(side="left", padx=5)
        ttk.Button(control_frame, text="View Transcripts", command=self._view_transcripts).pack(side="left", padx=5)
        
        # Status area
        voice_info = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        voice_info.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        voice_info.insert(tk.END, "Voice Management\n\n")
        voice_info.insert(tk.END, "Use Discord commands to control voice features:\n")
        voice_info.insert(tk.END, "- /join - Join a voice channel\n")
        voice_info.insert(tk.END, "- /leave - Leave the voice channel\n")
        voice_info.insert(tk.END, "- /record - Start recording\n")
        voice_info.insert(tk.END, "- /stoprecord - Stop recording\n")
        voice_info.insert(tk.END, "- /transcripts - List transcripts\n\n")
        
        voice_info.insert(tk.END, "Voice Status:\n")
        
        # Safely check if voice manager exists and has the required methods
        if (hasattr(self.bot, 'voice_manager') and self.bot.voice_manager and 
            hasattr(self.bot.voice_manager, 'get_connected_guilds')):
            try:
                connected_guilds = self.bot.voice_manager.get_connected_guilds()
                if connected_guilds:
                    voice_info.insert(tk.END, f"Connected to {len(connected_guilds)} voice channel(s)\n")
                    for guild_id in connected_guilds:
                        guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                        guild_name = guild.name if guild else f"Unknown ({guild_id})"
                        recording = "Yes" if (hasattr(self.bot.voice_manager, 'is_recording') and 
                                              self.bot.voice_manager.is_recording(guild_id)) else "No"
                        voice_info.insert(tk.END, f"- {guild_name} (Recording: {recording})\n")
                else:
                    voice_info.insert(tk.END, "Not connected to any voice channels\n")
            except Exception as e:
                voice_info.insert(tk.END, f"Error getting voice status: {str(e)}\n")
                logger.error(f"Error getting voice status: {e}")
        else:
            voice_info.insert(tk.END, "Voice manager not available\n")
            if hasattr(self.bot, 'initialized_components') and not self.bot.initialized_components.get('voice', False):
                voice_info.insert(tk.END, "\nVoice component is disabled. Enable it in the Settings tab.")
        
        voice_info.config(state=tk.DISABLED)
        self.voice_info = voice_info
    
    def _start_recording(self):
        """Start recording callback"""
        try:
            # Safe check for voice manager
            if not hasattr(self.bot, 'voice_manager') or not self.bot.voice_manager:
                messagebox.showwarning("Not Available", "Voice manager is not available")
                return
                
            voice_manager = self.bot.voice_manager
            
            # Safe check for required method
            if not hasattr(voice_manager, 'get_connected_guilds'):
                messagebox.showwarning("Not Available", "Voice manager doesn't support this operation")
                return
                
            connected_guilds = voice_manager.get_connected_guilds()
            
            if not connected_guilds:
                messagebox.showinfo("Not Connected", "Not connected to any voice channels")
                return
                
            if len(connected_guilds) == 1:
                # Only one guild, start recording there
                guild_id = connected_guilds[0]
                
                # Safe check for event loop
                if not hasattr(self.bot, 'loop'):
                    messagebox.showwarning("Not Available", "Bot event loop not accessible")
                    return
                
                try:
                    asyncio.run_coroutine_threadsafe(
                        voice_manager.start_recording(guild_id),
                        self.bot.loop
                    )
                    messagebox.showinfo("Recording Started", "Recording started")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
                    logger.error(f"Error starting recording: {e}")
            else:
                # Multiple guilds, ask which one
                guild_selection = tk.Toplevel(self.root)
                guild_selection.title("Select Server")
                guild_selection.geometry("300x200")
                
                ttk.Label(guild_selection, text="Select server to record:").pack(padx=10, pady=10)
                
                guild_var = tk.StringVar()
                guild_dropdown = ttk.Combobox(guild_selection, textvariable=guild_var)
                guild_dropdown.pack(padx=10, pady=5, fill="x")
                
                # Get guild names
                guild_options = {}
                for guild_id in connected_guilds:
                    guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                    name = guild.name if guild else f"Unknown ({guild_id})"
                    guild_options[name] = guild_id
                
                guild_dropdown['values'] = list(guild_options.keys())
                
                def start_selected_recording():
                    selected = guild_var.get()
                    if selected in guild_options:
                        guild_id = guild_options[selected]
                        
                        # Safe check for event loop
                        if not hasattr(self.bot, 'loop'):
                            messagebox.showwarning("Not Available", "Bot event loop not accessible")
                            guild_selection.destroy()
                            return
                        
                        try:
                            asyncio.run_coroutine_threadsafe(
                                voice_manager.start_recording(guild_id),
                                self.bot.loop
                            )
                            messagebox.showinfo("Recording Started", f"Recording started in {selected}")
                            guild_selection.destroy()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
                            logger.error(f"Error starting recording: {e}")
                            guild_selection.destroy()
                
                ttk.Button(guild_selection, text="Start Recording", command=start_selected_recording).pack(pady=10)
                ttk.Button(guild_selection, text="Cancel", command=guild_selection.destroy).pack(pady=5)
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            messagebox.showerror("Error", f"Failed to start recording: {str(e)}")
    
    def _stop_recording(self):
        """Stop recording callback"""
        try:
            # Safe check for voice manager
            if not hasattr(self.bot, 'voice_manager') or not self.bot.voice_manager:
                messagebox.showwarning("Not Available", "Voice manager is not available")
                return
                
            voice_manager = self.bot.voice_manager
            recording_guilds = []
            
            # Safe check for required methods
            if not all(hasattr(voice_manager, attr) for attr in ['get_connected_guilds', 'is_recording']):
                messagebox.showwarning("Not Available", "Voice manager doesn't support this operation")
                return
            
            # Find guilds that are recording
            for guild_id in voice_manager.get_connected_guilds():
                if voice_manager.is_recording(guild_id):
                    recording_guilds.append(guild_id)
            
            if not recording_guilds:
                messagebox.showinfo("Not Recording", "Not recording in any voice channels")
                return
                
            if len(recording_guilds) == 1:
                # Only one guild recording, stop that one
                guild_id = recording_guilds[0]
                
                # Safe check for event loop
                if not hasattr(self.bot, 'loop'):
                    messagebox.showwarning("Not Available", "Bot event loop not accessible")
                    return
                
                try:
                    asyncio.run_coroutine_threadsafe(
                        voice_manager.stop_recording(guild_id),
                        self.bot.loop
                    )
                    messagebox.showinfo("Recording Stopped", "Recording stopped")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to stop recording: {str(e)}")
                    logger.error(f"Error stopping recording: {e}")
            else:
                # Multiple recordings, ask which one to stop
                guild_selection = tk.Toplevel(self.root)
                guild_selection.title("Select Server")
                guild_selection.geometry("300x200")
                
                ttk.Label(guild_selection, text="Select recording to stop:").pack(padx=10, pady=10)
                
                guild_var = tk.StringVar()
                guild_dropdown = ttk.Combobox(guild_selection, textvariable=guild_var)
                guild_dropdown.pack(padx=10, pady=5, fill="x")
                
                # Get guild names
                guild_options = {}
                for guild_id in recording_guilds:
                    guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                    name = guild.name if guild else f"Unknown ({guild_id})"
                    guild_options[name] = guild_id
                
                guild_dropdown['values'] = list(guild_options.keys())
                
                def stop_selected_recording():
                    selected = guild_var.get()
                    if selected in guild_options:
                        guild_id = guild_options[selected]
                        
                        # Safe check for event loop
                        if not hasattr(self.bot, 'loop'):
                            messagebox.showwarning("Not Available", "Bot event loop not accessible")
                            guild_selection.destroy()
                            return
                        
                        try:
                            asyncio.run_coroutine_threadsafe(
                                voice_manager.stop_recording(guild_id),
                                self.bot.loop
                            )
                            messagebox.showinfo("Recording Stopped", f"Recording stopped in {selected}")
                            guild_selection.destroy()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to stop recording: {str(e)}")
                            logger.error(f"Error stopping recording: {e}")
                            guild_selection.destroy()
                
                ttk.Button(guild_selection, text="Stop Recording", command=stop_selected_recording).pack(pady=10)
                ttk.Button(guild_selection, text="Cancel", command=guild_selection.destroy).pack(pady=5)
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            messagebox.showerror("Error", f"Failed to stop recording: {str(e)}")
    
    def _view_transcripts(self):
        """View transcripts callback"""
        try:
            # Safe check for voice manager
            if not hasattr(self.bot, 'voice_manager') or not self.bot.voice_manager:
                messagebox.showwarning("Not Available", "Voice manager is not available")
                return
                
            voice_manager = self.bot.voice_manager
            
            # Safe check for required method
            if not hasattr(voice_manager, 'get_connected_guilds'):
                messagebox.showwarning("Not Available", "Voice manager doesn't support this operation")
                return
                
            connected_guilds = voice_manager.get_connected_guilds()
            
            if not connected_guilds:
                messagebox.showinfo("Not Connected", "Not connected to any guilds")
                return
                
            if len(connected_guilds) == 1:
                # Only one guild, show transcripts for that one
                guild_id = connected_guilds[0]
                self._show_guild_transcripts(guild_id)
            else:
                # Multiple guilds, ask which one
                guild_selection = tk.Toplevel(self.root)
                guild_selection.title("Select Server")
                guild_selection.geometry("300x200")
                
                ttk.Label(guild_selection, text="Select server to view transcripts:").pack(padx=10, pady=10)
                
                guild_var = tk.StringVar()
                guild_dropdown = ttk.Combobox(guild_selection, textvariable=guild_var)
                guild_dropdown.pack(padx=10, pady=5, fill="x")
                
                # Get guild names
                guild_options = {}
                for guild_id in connected_guilds:
                    guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                    name = guild.name if guild else f"Unknown ({guild_id})"
                    guild_options[name] = guild_id
                
                guild_dropdown['values'] = list(guild_options.keys())
                
                def show_selected_guild_transcripts():
                    selected = guild_var.get()
                    if selected in guild_options:
                        guild_id = guild_options[selected]
                        guild_selection.destroy()
                        self._show_guild_transcripts(guild_id)
                
                ttk.Button(guild_selection, text="View Transcripts", command=show_selected_guild_transcripts).pack(pady=10)
                ttk.Button(guild_selection, text="Cancel", command=guild_selection.destroy).pack(pady=5)
        except Exception as e:
            logger.error(f"Error viewing transcripts: {e}")
            messagebox.showerror("Error", f"Failed to view transcripts: {str(e)}")
    
    def _show_guild_transcripts(self, guild_id):
        """Show transcripts for a specific guild"""
        try:
            # Check if get_session_transcripts is available
            if not hasattr(self.bot.voice_manager, 'get_session_transcripts'):
                messagebox.showwarning("Not Available", "Transcript browsing not available")
                return
                
            # Get transcripts through async call
            if not hasattr(self.bot, 'loop'):
                messagebox.showwarning("Not Available", "Bot event loop not accessible")
                return
                
            # Create a future to get the result from the coroutine
            future = asyncio.run_coroutine_threadsafe(
                self.bot.voice_manager.get_session_transcripts(guild_id),
                self.bot.loop
            )
            
            # Wait for the result (with timeout)
            try:
                transcripts = future.result(timeout=5)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to get transcripts: {str(e)}")
                logger.error(f"Error getting transcripts: {e}")
                return
                
            if not transcripts:
                messagebox.showinfo("No Transcripts", "No transcripts found for this server")
                return
                
            # Create a transcript browser window
            browser = tk.Toplevel(self.root)
            browser.title("Transcript Browser")
            browser.geometry("700x500")
            
            # Layout
            browser.columnconfigure(0, weight=1)
            browser.rowconfigure(0, weight=0)  # Header
            browser.rowconfigure(1, weight=1)  # Content
            
            # Header
            header = ttk.Frame(browser)
            header.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            
            ttk.Label(header, text="Select a transcript:", font=("TkDefaultFont", 11)).pack(side="left", padx=5)
            
            # Create a dropdown for transcript selection
            transcript_var = tk.StringVar()
            transcript_combo = ttk.Combobox(header, textvariable=transcript_var, width=50)
            transcript_combo.pack(side="left", padx=5, expand=True, fill="x")
            
            # Populate dropdown with transcript names
            transcript_options = {}
            for transcript in transcripts:
                name = f"{transcript['date']} - {transcript['filename']}"
                transcript_options[name] = transcript['path']
            
            transcript_combo['values'] = list(transcript_options.keys())
            if transcript_combo['values']:
                transcript_combo.current(0)
            
            # Content area for transcript
            content_frame = ttk.Frame(browser)
            content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
            content_frame.columnconfigure(0, weight=1)
            content_frame.rowconfigure(0, weight=1)
            
            transcript_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD)
            transcript_text.grid(row=0, column=0, sticky="nsew")
            
            # Function to load selected transcript
            def load_selected_transcript():
                selected = transcript_var.get()
                if selected in transcript_options:
                    path = transcript_options[selected]
                    
                    # Get transcript content through async call
                    if not hasattr(self.bot, 'loop') or not hasattr(self.bot.voice_manager, 'read_transcript'):
                        messagebox.showwarning("Not Available", "Transcript reading not available")
                        return
                        
                    # Create a future to get the result from the coroutine
                    future = asyncio.run_coroutine_threadsafe(
                        self.bot.voice_manager.read_transcript(path),
                        self.bot.loop
                    )
                    
                    # Wait for the result (with timeout)
                    try:
                        content = future.result(timeout=5)
                        
                        # Update the text area
                        transcript_text.delete(1.0, tk.END)
                        if content:
                            transcript_text.insert(tk.END, content)
                        else:
                            transcript_text.insert(tk.END, "Failed to read transcript or transcript is empty.")
                    except Exception as e:
                        transcript_text.delete(1.0, tk.END)
                        transcript_text.insert(tk.END, f"Error reading transcript: {str(e)}")
                        logger.error(f"Error reading transcript: {e}")
            
            # Add a button to load the transcript
            ttk.Button(header, text="Load", command=load_selected_transcript).pack(side="right", padx=5)
            
            # Load the first transcript automatically
            if transcript_options:
                load_selected_transcript()
                
        except Exception as e:
            logger.error(f"Error showing guild transcripts: {e}")
            messagebox.showerror("Error", f"Failed to show transcripts: {str(e)}")
    
    def _setup_audio_tab(self, parent):
        """Set up the audio tab with enhanced group management"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Controls
        parent.rowconfigure(1, weight=1)  # Main content area
        
        # Control frame
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(control_frame, text="Play", command=self._play_audio).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Pause", command=self._pause_audio).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Stop", command=self._stop_audio).pack(side="left", padx=5)
        
        # Volume control
        ttk.Label(control_frame, text="Volume:").pack(side="left", padx=(20, 5))
        self.volume_var = tk.IntVar(value=50)
        volume_scale = ttk.Scale(control_frame, from_=0, to=100, variable=self.volume_var, 
                                 command=self._set_volume)
        volume_scale.pack(side="left", padx=5, fill="x", expand=True)
        
        # Main content area with split panes
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=3)
        content_frame.rowconfigure(0, weight=1)
        
        # Groups panel (left)
        groups_frame = ttk.LabelFrame(content_frame, text="Audio Groups")
        groups_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        
        groups_frame.columnconfigure(0, weight=1)
        groups_frame.rowconfigure(0, weight=1)
        groups_frame.rowconfigure(1, weight=0)
        
        # Groups listbox with scrollbar
        groups_list_frame = ttk.Frame(groups_frame)
        groups_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        groups_listbox = tk.Listbox(groups_list_frame)
        groups_scrollbar = ttk.Scrollbar(groups_list_frame, orient="vertical", command=groups_listbox.yview)
        groups_listbox.configure(yscrollcommand=groups_scrollbar.set)
        
        groups_scrollbar.pack(side="right", fill="y")
        groups_listbox.pack(side="left", fill="both", expand=True)
        
        self.audio_groups_listbox = groups_listbox
        
        # Group management buttons
        group_buttons_frame = ttk.Frame(groups_frame)
        group_buttons_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        ttk.Button(group_buttons_frame, text="New Group", command=self._create_audio_group).pack(side="left", padx=2, expand=True, fill="x")
        ttk.Button(group_buttons_frame, text="Delete", command=self._delete_audio_group).pack(side="right", padx=2, expand=True, fill="x")
        
        # Files panel (right)
        files_frame = ttk.LabelFrame(content_frame, text="Audio Files")
        files_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        files_frame.rowconfigure(1, weight=0)
        
        # Files listbox with scrollbar
        files_list_frame = ttk.Frame(files_frame)
        files_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        files_listbox = tk.Listbox(files_list_frame)
        files_scrollbar = ttk.Scrollbar(files_list_frame, orient="vertical", command=files_listbox.yview)
        files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        files_scrollbar.pack(side="right", fill="y")
        files_listbox.pack(side="left", fill="both", expand=True)
        
        self.audio_files_listbox = files_listbox
        
        # Files management buttons
        file_buttons_frame = ttk.Frame(files_frame)
        file_buttons_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        ttk.Button(file_buttons_frame, text="Upload", command=self._upload_audio_file).pack(side="left", padx=2, expand=True, fill="x")
        ttk.Button(file_buttons_frame, text="Play", command=self._play_selected_audio).pack(side="left", padx=2, expand=True, fill="x")
        ttk.Button(file_buttons_frame, text="Delete", command=self._delete_audio_file).pack(side="right", padx=2, expand=True, fill="x")
        
        # Load initial groups
        self._load_audio_groups()
        
        # Bind selection event
        groups_listbox.bind("<<ListboxSelect>>", self._on_audio_group_selected)
    
    def _load_audio_groups(self):
        """Load audio groups"""
        try:
            self.audio_groups_listbox.delete(0, tk.END)
            self.audio_files_listbox.delete(0, tk.END)
            
            # Standard categories
            default_groups = ["Default", "Combat", "Ambience", "Music", "Effects"]
            
            # Add categories to listbox
            for group in default_groups:
                self.audio_groups_listbox.insert(tk.END, group)
            
            # Try to load custom groups if available
            custom_groups_file = "data/audio/custom_groups.json"
            if os.path.exists(custom_groups_file):
                try:
                    with open(custom_groups_file, 'r') as f:
                        custom_groups = json.load(f)
                        for group in custom_groups:
                            if group not in default_groups:
                                self.audio_groups_listbox.insert(tk.END, group)
                except Exception as e:
                    logger.error(f"Error loading custom audio groups: {e}")
        except Exception as e:
            logger.error(f"Error loading audio groups: {e}")
    
    def _create_audio_group(self):
        """Create a new audio group"""
        try:
            # Ask for group name
            group_name = simpledialog.askstring("New Group", "Enter name for the new audio group:", parent=self.root)
            
            if not group_name:
                return
                
            # Validate name - no special characters
            if not all(c.isalnum() or c.isspace() for c in group_name):
                messagebox.showwarning("Invalid Name", "Group name can only contain letters, numbers, and spaces")
                return
            
            # Check if group already exists
            existing_groups = list(self.audio_groups_listbox.get(0, tk.END))
            if group_name in existing_groups:
                messagebox.showwarning("Duplicate", f"A group named '{group_name}' already exists")
                return
            
            # Add to listbox
            self.audio_groups_listbox.insert(tk.END, group_name)
            
            # Create directory for the group
            group_dir = f"data/audio/soundboard/{group_name}"
            os.makedirs(group_dir, exist_ok=True)
            
            # Save custom groups
            self._save_custom_audio_groups()
            
            messagebox.showinfo("Success", f"Created new audio group: {group_name}")
            
        except Exception as e:
            logger.error(f"Error creating audio group: {e}")
            messagebox.showerror("Error", f"Failed to create audio group: {str(e)}")
    
    def _delete_audio_group(self):
        """Delete selected audio group"""
        try:
            # Get selected group
            selection = self.audio_groups_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a group to delete")
                return
                
            group_name = self.audio_groups_listbox.get(selection[0])
            
            # Don't allow deleting default groups
            default_groups = ["Default", "Combat", "Ambience"]
            if group_name in default_groups:
                messagebox.showwarning("Protected", f"Cannot delete the default group '{group_name}'")
                return
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Really delete the group '{group_name}' and all its audio files?"):
                return
            
            # Delete the group directory
            group_dir = f"data/audio/soundboard/{group_name}"
            if os.path.exists(group_dir):
                shutil.rmtree(group_dir)
            
            # Remove from listbox
            self.audio_groups_listbox.delete(selection[0])
            
            # Clear files list
            self.audio_files_listbox.delete(0, tk.END)
            
            # Save custom groups
            self._save_custom_audio_groups()
            
            messagebox.showinfo("Success", f"Deleted audio group: {group_name}")
            
        except Exception as e:
            logger.error(f"Error deleting audio group: {e}")
            messagebox.showerror("Error", f"Failed to delete audio group: {str(e)}")
    
    def _save_custom_audio_groups(self):
        """Save custom audio groups to JSON file"""
        try:
            # Get all groups from listbox
            all_groups = list(self.audio_groups_listbox.get(0, tk.END))
            
            # Filter out default groups
            default_groups = ["Default", "Combat", "Ambience"]
            custom_groups = [g for g in all_groups if g not in default_groups]
            
            # Save to JSON
            custom_groups_file = "data/audio/custom_groups.json"
            os.makedirs(os.path.dirname(custom_groups_file), exist_ok=True)
            
            with open(custom_groups_file, 'w') as f:
                json.dump(custom_groups, f)
                
        except Exception as e:
            logger.error(f"Error saving custom audio groups: {e}")
    
    def _on_audio_group_selected(self, event):
        """Handle audio group selection"""
        try:
            # Get selected group
            selection = self.audio_groups_listbox.curselection()
            if not selection:
                return
                
            group_name = self.audio_groups_listbox.get(selection[0])
            
            # Load files for this group
            self._load_audio_files(group_name)
            
        except Exception as e:
            logger.error(f"Error handling audio group selection: {e}")
    
    def _load_audio_files(self, group_name):
        """Load audio files for a group"""
        try:
            self.audio_files_listbox.delete(0, tk.END)
            
            # Get files in the group directory
            group_dir = f"data/audio/soundboard/{group_name}"
            if not os.path.exists(group_dir):
                return
                
            # List files with audio extensions
            audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
            files = [f for f in os.listdir(group_dir) if f.lower().endswith(audio_extensions)]
            
            # Add to listbox
            for file in sorted(files):
                self.audio_files_listbox.insert(tk.END, file)
                
        except Exception as e:
            logger.error(f"Error loading audio files: {e}")
    
    def _upload_audio_file(self):
        """Upload a new audio file"""
        try:
            # Get selected group
            group_selection = self.audio_groups_listbox.curselection()
            if not group_selection:
                messagebox.showinfo("No Selection", "Please select a group to upload to")
                return
                
            group_name = self.audio_groups_listbox.get(group_selection[0])
            
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=[
                    ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
                    ("All Files", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # Get just the filename
            file_name = os.path.basename(file_path)
            
            # Copy file to group directory
            group_dir = f"data/audio/soundboard/{group_name}"
            os.makedirs(group_dir, exist_ok=True)
            
            # Check if file already exists
            if os.path.exists(os.path.join(group_dir, file_name)):
                if not messagebox.askyesno("File Exists", f"The file '{file_name}' already exists. Replace it?"):
                    return
            
            # Copy the file
            shutil.copy2(file_path, os.path.join(group_dir, file_name))
            
            # Reload files
            self._load_audio_files(group_name)
            
            messagebox.showinfo("Success", f"Uploaded '{file_name}' to group '{group_name}'")
            
        except Exception as e:
            logger.error(f"Error uploading audio file: {e}")
            messagebox.showerror("Error", f"Failed to upload audio file: {str(e)}")
    
    def _play_selected_audio(self):
        """Play the selected audio file"""
        try:
            # Get selected group and file
            group_selection = self.audio_groups_listbox.curselection()
            file_selection = self.audio_files_listbox.curselection()
            
            if not group_selection or not file_selection:
                messagebox.showinfo("No Selection", "Please select a group and file to play")
                return
                
            group_name = self.audio_groups_listbox.get(group_selection[0])
            file_name = self.audio_files_listbox.get(file_selection[0])
            
            # This would normally call bot.audio_manager.play_sound with the file
            messagebox.showinfo("Play Audio", f"Playing '{file_name}' from group '{group_name}'")
            
        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
            messagebox.showerror("Error", f"Failed to play audio file: {str(e)}")
    
    def _delete_audio_file(self):
        """Delete selected audio file"""
        try:
            # Get selected group and file
            group_selection = self.audio_groups_listbox.curselection()
            file_selection = self.audio_files_listbox.curselection()
            
            if not group_selection or not file_selection:
                messagebox.showinfo("No Selection", "Please select a group and file to delete")
                return
                
            group_name = self.audio_groups_listbox.get(group_selection[0])
            file_name = self.audio_files_listbox.get(file_selection[0])
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Really delete the file '{file_name}'?"):
                return
            
            # Delete the file
            file_path = os.path.join(f"data/audio/soundboard/{group_name}", file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Reload files
            self._load_audio_files(group_name)
            
            messagebox.showinfo("Success", f"Deleted '{file_name}'")
            
        except Exception as e:
            logger.error(f"Error deleting audio file: {e}")
            messagebox.showerror("Error", f"Failed to delete audio file: {str(e)}")
    
    def _play_audio(self):
        """Play audio callback"""
        messagebox.showinfo("Feature Coming Soon", "Audio playback from the control panel will be available in the next update.")
    
    def _pause_audio(self):
        """Pause audio callback"""
        messagebox.showinfo("Feature Coming Soon", "Audio control from the control panel will be available in the next update.")
    
    def _stop_audio(self):
        """Stop audio callback"""
        messagebox.showinfo("Feature Coming Soon", "Audio control from the control panel will be available in the next update.")
    
    def _set_volume(self, value):
        """Set volume callback"""
        # Would use asyncio.run_coroutine_threadsafe to call audio_manager.set_volume with volume_var.get()/100.0
        pass
    
    def _setup_soundboard_tab(self, parent):
        """Set up the soundboard tab with category management"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Category management
        parent.rowconfigure(1, weight=1)  # Main content
        
        # Category management
        category_mgmt_frame = ttk.Frame(parent)
        category_mgmt_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(category_mgmt_frame, text="Manage Categories:").pack(side="left", padx=5)
        ttk.Button(category_mgmt_frame, text="New Category", command=self._create_soundboard_category).pack(side="left", padx=5)
        ttk.Button(category_mgmt_frame, text="Delete Category", command=self._delete_soundboard_category).pack(side="left", padx=5)
        ttk.Button(category_mgmt_frame, text="Add Sound", command=self._add_soundboard_sound).pack(side="left", padx=5)
        ttk.Button(category_mgmt_frame, text="Delete Sound", command=self._delete_soundboard_sound).pack(side="left", padx=5)
        
        # Main content with split panes
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        content_frame.columnconfigure(0, weight=0)  # Categories
        content_frame.columnconfigure(1, weight=1)  # Sounds
        content_frame.rowconfigure(0, weight=1)
        
        # Categories frame
        categories_frame = ttk.LabelFrame(content_frame, text="Categories")
        categories_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ns")
        
        # Category buttons
        self.category_var = tk.StringVar(value="Default")
        categories = ["Default", "Combat", "Ambience", "Custom"]
        
        # Try to load custom categories
        custom_categories_file = "data/audio/custom_categories.json"
        if os.path.exists(custom_categories_file):
            try:
                with open(custom_categories_file, 'r') as f:
                    custom_categories = json.load(f)
                    for category in custom_categories:
                        if category not in categories:
                            categories.append(category)
            except Exception as e:
                logger.error(f"Error loading custom categories: {e}")
        
        for i, category in enumerate(categories):
            ttk.Radiobutton(categories_frame, text=category, value=category, variable=self.category_var, 
                           command=self._load_sounds).pack(padx=10, pady=5, anchor="w")
        
        # Sounds frame with scrollbar
        sounds_container = ttk.LabelFrame(content_frame, text="Sounds")
        sounds_container.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        
        sounds_container.columnconfigure(0, weight=1)
        sounds_container.rowconfigure(0, weight=1)
        
        # Canvas for scrolling
        sounds_canvas = tk.Canvas(sounds_container, highlightthickness=0)
        sounds_scrollbar = ttk.Scrollbar(sounds_container, orient="vertical", command=sounds_canvas.yview)
        sounds_canvas.configure(yscrollcommand=sounds_scrollbar.set)
        
        sounds_scrollbar.grid(row=0, column=1, sticky="ns")
        sounds_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.sounds_frame = ttk.Frame(sounds_canvas)
        sounds_canvas.create_window((0, 0), window=self.sounds_frame, anchor="nw")
        
        self.sounds_frame.bind("<Configure>", lambda e: sounds_canvas.configure(scrollregion=sounds_canvas.bbox("all")))
        sounds_canvas.bind("<Configure>", lambda e: sounds_canvas.itemconfig(1, width=e.width))
        
        # Load sounds initially
        self._load_sounds()
    
    def _create_soundboard_category(self):
        """Create a new soundboard category"""
        try:
            # Ask for category name
            category_name = simpledialog.askstring("New Category", "Enter name for the new soundboard category:", parent=self.root)
            
            if not category_name:
                return
                
            # Validate name - no special characters
            if not all(c.isalnum() or c.isspace() for c in category_name):
                messagebox.showwarning("Invalid Name", "Category name can only contain letters, numbers, and spaces")
                return
            
            # Create directory for the category
            category_dir = f"data/audio/soundboard/{category_name}"
            os.makedirs(category_dir, exist_ok=True)
            
            # Add to custom categories JSON
            custom_categories_file = "data/audio/custom_categories.json"
            custom_categories = []
            
            if os.path.exists(custom_categories_file):
                try:
                    with open(custom_categories_file, 'r') as f:
                        custom_categories = json.load(f)
                except Exception:
                    custom_categories = []
            
            if category_name not in custom_categories:
                custom_categories.append(category_name)
                
                with open(custom_categories_file, 'w') as f:
                    json.dump(custom_categories, f)
            
            # Rebuild the soundboard tab
            messagebox.showinfo("Success", f"Created new soundboard category: {category_name}")
            self._setup_tab_control()  # This will rebuild all tabs
            
        except Exception as e:
            logger.error(f"Error creating soundboard category: {e}")
            messagebox.showerror("Error", f"Failed to create soundboard category: {str(e)}")
    
    def _delete_soundboard_category(self):
        """Delete a soundboard category"""
        try:
            # Get current category
            category_name = self.category_var.get()
            
            # Don't allow deleting default categories
            default_categories = ["Default", "Combat", "Ambience"]
            if category_name in default_categories:
                messagebox.showwarning("Protected", f"Cannot delete the default category '{category_name}'")
                return
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Really delete the category '{category_name}' and all its sounds?"):
                return
            
            # Delete the category directory
            category_dir = f"data/audio/soundboard/{category_name}"
            if os.path.exists(category_dir):
                shutil.rmtree(category_dir)
            
            # Remove from custom categories JSON
            custom_categories_file = "data/audio/custom_categories.json"
            if os.path.exists(custom_categories_file):
                try:
                    with open(custom_categories_file, 'r') as f:
                        custom_categories = json.load(f)
                        
                    if category_name in custom_categories:
                        custom_categories.remove(category_name)
                        
                        with open(custom_categories_file, 'w') as f:
                            json.dump(custom_categories, f)
                except Exception as e:
                    logger.error(f"Error updating custom categories: {e}")
            
            # Rebuild the soundboard tab
            messagebox.showinfo("Success", f"Deleted soundboard category: {category_name}")
            self._setup_tab_control()  # This will rebuild all tabs
            
        except Exception as e:
            logger.error(f"Error deleting soundboard category: {e}")
            messagebox.showerror("Error", f"Failed to delete soundboard category: {str(e)}")
    
    def _add_soundboard_sound(self):
        """Add a sound to the current soundboard category"""
        try:
            # Get current category
            category_name = self.category_var.get()
            
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Sound File",
                filetypes=[
                    ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
                    ("All Files", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # Get just the filename
            file_name = os.path.basename(file_path)
            
            # Copy file to category directory
            category_dir = f"data/audio/soundboard/{category_name}"
            os.makedirs(category_dir, exist_ok=True)
            
            # Check if file already exists
            if os.path.exists(os.path.join(category_dir, file_name)):
                if not messagebox.askyesno("File Exists", f"The file '{file_name}' already exists. Replace it?"):
                    return
            
            # Copy the file
            shutil.copy2(file_path, os.path.join(category_dir, file_name))
            
            # Reload sounds
            self._load_sounds()
            
            messagebox.showinfo("Success", f"Added sound '{file_name}' to category '{category_name}'")
            
        except Exception as e:
            logger.error(f"Error adding soundboard sound: {e}")
            messagebox.showerror("Error", f"Failed to add soundboard sound: {str(e)}")
    
    def _delete_soundboard_sound(self):
        """Delete a sound from the current soundboard category"""
        try:
            # Get current category
            category_name = self.category_var.get()
            
            # Find which sound button is selected - this is a bit tricky since we're using a grid of buttons
            # Let's use a selection dialog instead
            sound_files = []
            category_dir = f"data/audio/soundboard/{category_name}"
            
            if os.path.exists(category_dir):
                # List audio files
                audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
                sound_files = [f for f in os.listdir(category_dir) if f.lower().endswith(audio_extensions)]
            
            if not sound_files:
                messagebox.showinfo("No Sounds", f"No sounds found in category '{category_name}'")
                return
            
            # Create a selection dialog
            selection_dialog = tk.Toplevel(self.root)
            selection_dialog.title(f"Select Sound to Delete - {category_name}")
            selection_dialog.geometry("400x300")
            
            ttk.Label(selection_dialog, text=f"Select a sound to delete from '{category_name}':", 
                     wraplength=380).pack(padx=10, pady=10)
            
            # Create listbox with scrollbar
            frame = ttk.Frame(selection_dialog)
            frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            listbox = tk.Listbox(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side="right", fill="y")
            listbox.pack(side="left", fill="both", expand=True)
            
            # Add sound files to listbox
            for sound in sorted(sound_files):
                listbox.insert(tk.END, sound)
            
            def delete_selected_sound():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("No Selection", "Please select a sound to delete", parent=selection_dialog)
                    return
                
                sound_name = listbox.get(selection[0])
                
                # Confirm deletion
                if not messagebox.askyesno("Confirm Delete", f"Really delete the sound '{sound_name}'?", 
                                         parent=selection_dialog):
                    return
                
                # Delete the file
                file_path = os.path.join(category_dir, sound_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Close dialog
                selection_dialog.destroy()
                
                # Reload sounds
                self._load_sounds()
                
                messagebox.showinfo("Success", f"Deleted sound '{sound_name}'")
            
            # Add buttons
            button_frame = ttk.Frame(selection_dialog)
            button_frame.pack(pady=10, fill="x")
            
            ttk.Button(button_frame, text="Delete Sound", command=delete_selected_sound).pack(side="left", padx=10)
            ttk.Button(button_frame, text="Cancel", command=selection_dialog.destroy).pack(side="right", padx=10)
            
        except Exception as e:
            logger.error(f"Error deleting soundboard sound: {e}")
            messagebox.showerror("Error", f"Failed to delete soundboard sound: {str(e)}")
    
    def _load_sounds(self):
        """Load sounds for the selected category"""
        category = self.category_var.get()
        
        # Clear existing sound buttons
        for widget in self.sounds_frame.winfo_children():
            widget.destroy()
        self.sound_buttons = {}
        
        # Get sounds for the category
        sounds = []
        try:
            # First check if we can get sounds from the audio manager
            if hasattr(self.bot, 'audio_manager') and self.bot.audio_manager and hasattr(self.bot.audio_manager, 'get_sounds_in_category'):
                sounds = self.bot.audio_manager.get_sounds_in_category(category)
            else:
                # Fallback to direct file system access
                category_dir = f"data/audio/soundboard/{category}"
                if os.path.exists(category_dir):
                    # List audio files
                    audio_extensions = ('.mp3', '.wav', '.ogg', '.flac')
                    sound_files = [f for f in os.listdir(category_dir) if f.lower().endswith(audio_extensions)]
                    
                    # Create sound objects
                    sounds = [type('Sound', (), {'name': os.path.splitext(f)[0], 'file_path': os.path.join(category_dir, f)}) 
                             for f in sound_files]
        except Exception as e:
            logger.error(f"Error loading sounds: {e}")
            ttk.Label(self.sounds_frame, text=f"Error loading sounds: {str(e)}").grid(padx=10, pady=10)
            return
        
        # Create buttons for each sound
        if sounds:
            # Configure the frame for button grid
            self.sounds_frame.columnconfigure(0, weight=1)
            self.sounds_frame.columnconfigure(1, weight=1)
            self.sounds_frame.columnconfigure(2, weight=1)
            
            # Add buttons
            for i, sound in enumerate(sorted(sounds, key=lambda s: getattr(s, 'name', str(s)))):
                row = i // 3
                col = i % 3
                
                # Fix lambda capture
                sound_name = getattr(sound, 'name', str(sound))
                button = ttk.Button(self.sounds_frame, text=sound_name, 
                                    command=lambda s=sound: self._play_sound(s))
                button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                self.sound_buttons[sound_name] = button
        else:
            ttk.Label(self.sounds_frame, text=f"No sounds found in category: {category}").grid(padx=10, pady=10)
    
    def _play_sound(self, sound):
        """Play a sound from the soundboard"""
        try:
            # Safe check for audio manager
            if not hasattr(self.bot, 'audio_manager') or not self.bot.audio_manager:
                messagebox.showwarning("Not Available", "Audio manager is not available")
                return
                
            audio_manager = self.bot.audio_manager
            
            # Safe check for voice_clients dictionary
            if not hasattr(audio_manager, 'voice_clients'):
                messagebox.showwarning("Not Available", "Audio manager doesn't support this operation")
                return
                
            connected_guilds = audio_manager.voice_clients.keys()
            
            if not connected_guilds:
                messagebox.showinfo("Not Connected", "Not connected to any voice channels")
                return
            
            # If multiple guilds, ask which one to play in
            if len(connected_guilds) > 1:
                guild_selection = tk.Toplevel(self.root)
                guild_selection.title("Select Server")
                guild_selection.geometry("300x200")
                
                ttk.Label(guild_selection, text="Select server to play sound in:").pack(padx=10, pady=10)
                
                guild_var = tk.StringVar()
                guild_dropdown = ttk.Combobox(guild_selection, textvariable=guild_var)
                guild_dropdown.pack(padx=10, pady=5, fill="x")
                
                # Get guild names
                guild_options = {}
                for guild_id in connected_guilds:
                    guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                    name = guild.name if guild else f"Unknown ({guild_id})"
                    guild_options[name] = guild_id
                
                guild_dropdown['values'] = list(guild_options.keys())
                if guild_dropdown['values']:
                    guild_dropdown.current(0)
                
                def play_in_selected_guild():
                    selected = guild_var.get()
                    if selected in guild_options:
                        guild_id = guild_options[selected]
                        sound_name = getattr(sound, 'name', str(sound))
                        category = self.category_var.get()
                        
                        # Safe check for event loop
                        if not hasattr(self.bot, 'loop'):
                            messagebox.showwarning("Not Available", "Bot event loop not accessible", parent=guild_selection)
                            guild_selection.destroy()
                            return
                        
                        try:
                            # Safe check for play_sound method
                            if hasattr(audio_manager, 'play_sound'):
                                asyncio.run_coroutine_threadsafe(
                                    audio_manager.play_sound(guild_id, sound_name, category),
                                    self.bot.loop
                                )
                                messagebox.showinfo("Playing", f"Playing sound '{sound_name}' in {selected}")
                            else:
                                messagebox.showinfo("Not Supported", "Sound playback not supported by this bot version")
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to play sound: {str(e)}", parent=guild_selection)
                            logger.error(f"Error playing sound: {e}")
                        
                        guild_selection.destroy()
                
                ttk.Button(guild_selection, text="Play", command=play_in_selected_guild).pack(pady=10)
                ttk.Button(guild_selection, text="Cancel", command=guild_selection.destroy).pack(pady=5)
            else:
                # Only one guild, play there
                guild_id = next(iter(connected_guilds))
                sound_name = getattr(sound, 'name', str(sound))
                category = self.category_var.get()
                
                # Safe check for event loop
                if not hasattr(self.bot, 'loop'):
                    messagebox.showwarning("Not Available", "Bot event loop not accessible")
                    return
                
                try:
                    guild = self.bot.get_guild(guild_id) if hasattr(self.bot, 'get_guild') else None
                    guild_name = guild.name if guild else f"Unknown ({guild_id})"
                    
                    # Safe check for play_sound method
                    if hasattr(audio_manager, 'play_sound'):
                        asyncio.run_coroutine_threadsafe(
                            audio_manager.play_sound(guild_id, sound_name, category),
                            self.bot.loop
                        )
                        messagebox.showinfo("Playing", f"Playing sound '{sound_name}' in {guild_name}")
                    else:
                        messagebox.showinfo("Not Supported", "Sound playback not supported by this bot version")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to play sound: {str(e)}")
                    logger.error(f"Error playing sound: {e}")
        except Exception as e:
            logger.error(f"Error playing sound: {e}")
            messagebox.showerror("Error", f"Failed to play sound: {str(e)}")
    
    def _setup_menu_tab(self, parent):
        """Set up the menu tab with command interface"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Server selector
        parent.rowconfigure(1, weight=1)  # Command area
        parent.rowconfigure(2, weight=1)  # Commands list
        
        # Server selector
        server_frame = ttk.Frame(parent)
        server_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(server_frame, text="Send command to server:").pack(side="left", padx=5)
        
        # Create server dropdown
        self.menu_server_var = tk.StringVar()
        self.menu_server_combo = ttk.Combobox(server_frame, textvariable=self.menu_server_var, width=30)
        self.menu_server_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        # Populate server dropdown
        self._update_menu_server_list()
        
        # Refresh button
        ttk.Button(server_frame, text="Refresh", command=self._update_menu_server_list).pack(side="right", padx=5)
        
        # Command input area
        command_frame = ttk.LabelFrame(parent, text="Command Input")
        command_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        command_frame.columnconfigure(0, weight=1)
        command_frame.rowconfigure(0, weight=0)  # Input
        command_frame.rowconfigure(1, weight=1)  # Output
        
        # Command input with slash prefix
        input_frame = ttk.Frame(command_frame)
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(input_frame, text="/").pack(side="left")
        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side="left", padx=0, fill="x", expand=True)
        ttk.Button(input_frame, text="Send", command=self._send_command).pack(side="right", padx=5)
        
        # Response output
        output_frame = ttk.Frame(command_frame)
        output_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.command_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=6)
        self.command_output.grid(row=0, column=0, sticky="nsew")
        self.command_output.insert(tk.END, "Command output will appear here...\n")
        
        # Commands list
        commands_frame = ttk.LabelFrame(parent, text="Available Commands")
        commands_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        commands_list = scrolledtext.ScrolledText(commands_frame, wrap=tk.WORD)
        commands_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load commands
        commands_list.insert(tk.END, "GENERAL COMMANDS:\n")
        commands_list.insert(tk.END, "/help - Show available commands\n")
        commands_list.insert(tk.END, "/info - Show bot information\n")
        commands_list.insert(tk.END, "/ping - Check bot latency\n\n")
        
        commands_list.insert(tk.END, "VOICE COMMANDS:\n")
        commands_list.insert(tk.END, "/join - Join a voice channel\n")
        commands_list.insert(tk.END, "/leave - Leave the voice channel\n")
        commands_list.insert(tk.END, "/record - Start recording the voice channel\n")
        commands_list.insert(tk.END, "/stoprecord - Stop recording\n")
        commands_list.insert(tk.END, "/transcripts - List available transcripts\n")
        commands_list.insert(tk.END, "/readtranscript <number> - Read a specific transcript\n\n")
        
        commands_list.insert(tk.END, "AUDIO COMMANDS:\n")
        commands_list.insert(tk.END, "/play <sound> [category] - Play a sound from the soundboard\n")
        commands_list.insert(tk.END, "/stop - Stop audio playback\n")
        commands_list.insert(tk.END, "/soundboard [category] - Show available sounds\n\n")
        
        commands_list.insert(tk.END, "ADMIN COMMANDS:\n")
        commands_list.insert(tk.END, "/sync - Force sync commands with Discord (Admin Only)\n")
        
        commands_list.config(state=tk.DISABLED)
    
    def _update_menu_server_list(self):
        """Update the server list in the menu tab"""
        # Clear current list
        self.menu_server_combo['values'] = []
        
        # Get guilds
        if not hasattr(self.bot, 'guilds'):
            return
            
        # Create mapping of guild names to IDs
        guild_options = {}
        for guild in self.bot.guilds:
            guild_options[guild.name] = guild.id
        
        # Update dropdown
        self.menu_server_combo['values'] = list(guild_options.keys())
        if self.menu_server_combo['values']:
            self.menu_server_combo.current(0)
    
    def _send_command(self):
        """Send a command to the selected server"""
        # Get command
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Get selected server
        server_name = self.menu_server_var.get()
        if not server_name:
            messagebox.showwarning("No Server", "Please select a server to send the command to")
            return
        
        # Find server ID
        server_id = None
        for guild in self.bot.guilds:
            if guild.name == server_name:
                server_id = guild.id
                break
        
        if not server_id:
            messagebox.showwarning("Server Not Found", "Could not find the selected server")
            return
        
        # Clear output and show command
        self.command_output.delete(1.0, tk.END)
        self.command_output.insert(tk.END, f"Executing command: /{command}\n")
        
        # Execute command
        messagebox.showinfo("Command Sent", f"Sent command: /{command} to {server_name}")
        
        # For now, just show a message - in a full implementation, we would use
        # asyncio.run_coroutine_threadsafe to call bot methods that execute commands
        self.command_output.insert(tk.END, "Command execution feature will be available in the next update.\n")
        self.command_output.insert(tk.END, "For now, use Discord's interface to execute commands.\n")
    
    def _setup_settings_tab(self, parent):
        """Set up the settings tab with component enablement"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # General settings
        parent.rowconfigure(1, weight=0)  # Component settings
        parent.rowconfigure(2, weight=0)  # Voice settings
        parent.rowconfigure(3, weight=0)  # Audio settings
        parent.rowconfigure(4, weight=1)  # Extra space
        
        # General settings
        general_frame = ttk.LabelFrame(parent, text="General Settings")
        general_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(general_frame, text="Bot Version:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(general_frame, text="Bishop Bot v0.1.0").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(general_frame, text="Created By:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(general_frame, text="Bioku87").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Component settings
        component_frame = ttk.LabelFrame(parent, text="Component Settings")
        component_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Get current component status
        component_status = {}
        if hasattr(self.bot, 'initialized_components'):
            component_status = self.bot.initialized_components
        
        # Database component
        ttk.Label(component_frame, text="Database:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        db_status = component_status.get('database', False)
        db_status_label = ttk.Label(component_frame, text="✅ Enabled" if db_status else "❌ Disabled")
        db_status_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        db_button_text = "Disable" if db_status else "Enable"
        ttk.Button(component_frame, text=db_button_text, command=self._toggle_database).grid(
            row=0, column=2, sticky="e", padx=10, pady=5)
        
        # Voice component
        ttk.Label(component_frame, text="Voice:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        voice_status = component_status.get('voice', False)
        voice_status_label = ttk.Label(component_frame, text="✅ Enabled" if voice_status else "❌ Disabled")
        voice_status_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        voice_button_text = "Disable" if voice_status else "Enable"
        ttk.Button(component_frame, text=voice_button_text, command=self._toggle_voice).grid(
            row=1, column=2, sticky="e", padx=10, pady=5)
        
        # Audio component
        ttk.Label(component_frame, text="Audio:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        audio_status = component_status.get('audio', False)
        audio_status_label = ttk.Label(component_frame, text="✅ Enabled" if audio_status else "❌ Disabled")
        audio_status_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        audio_button_text = "Disable" if audio_status else "Enable"
        ttk.Button(component_frame, text=audio_button_text, command=self._toggle_audio).grid(
            row=2, column=2, sticky="e", padx=10, pady=5)
        
        # Store labels for updates
        self.component_status_labels = {
            'database': db_status_label,
            'voice': voice_status_label,
            'audio': audio_status_label
        }
        
        # Voice settings
        voice_frame = ttk.LabelFrame(parent, text="Voice Settings")
        voice_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(voice_frame, text="Transcription Engine:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        engine_var = tk.StringVar(value="Whisper")
        ttk.Combobox(voice_frame, textvariable=engine_var, values=["Whisper", "Google", "Azure"], 
                    state="readonly").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(voice_frame, text="Whisper Model:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        model_var = tk.StringVar(value="base.en")
        ttk.Combobox(voice_frame, textvariable=model_var, values=["tiny.en", "base.en", "small.en", "medium.en"], 
                   state="readonly").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Button(voice_frame, text="Apply Voice Settings", command=self._apply_voice_settings).grid(
            row=2, column=1, sticky="e", padx=10, pady=5)
        
        # Audio settings
        audio_frame = ttk.LabelFrame(parent, text="Audio Settings")
        audio_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Label(audio_frame, text="Default Volume:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        volume_var = tk.IntVar(value=50)
        ttk.Scale(audio_frame, from_=0, to=100, variable=volume_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        ttk.Button(audio_frame, text="Apply Audio Settings", command=self._apply_audio_settings).grid(
            row=1, column=1, sticky="e", padx=10, pady=5)
    
    def _toggle_database(self):
        """Toggle database component"""
        if not hasattr(self.bot, 'initialized_components'):
            messagebox.showwarning("Not Available", "Component management not available")
            return
            
        current_status = self.bot.initialized_components.get('database', False)
        
        if current_status:
            messagebox.showinfo("Database", "Database component will remain enabled - disabling is not supported")
        else:
            try:
                messagebox.showinfo("Database", "Initializing database component...")
                
                # Attempt to initialize the database component
                try:
                    # Add src directory to path to help with imports
                    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                    from database.manager import DatabaseManager
                    self.bot.db = DatabaseManager()
                    self.bot.initialized_components['database'] = True
                    self.component_status_labels['database'].config(text="✅ Enabled")
                    messagebox.showinfo("Success", "Database component enabled successfully")
                except ImportError:
                    # Create and initialize a minimal database manager
                    db_path = "data/database"
                    os.makedirs(db_path, exist_ok=True)
                    
                    # Create a simple SQLite DB file
                    import sqlite3
                    conn = sqlite3.connect(f"{db_path}/bishop.db")
                    cursor = conn.cursor()
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_data (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                    ''')
                    conn.commit()
                    conn.close()
                    
                    # Update status
                    self.bot.initialized_components['database'] = True
                    self.component_status_labels['database'].config(text="✅ Enabled")
                    messagebox.showinfo("Success", "Basic database component enabled")
            except Exception as e:
                logger.error(f"Error enabling database: {e}")
                messagebox.showerror("Error", f"Failed to enable database: {str(e)}")
    
    def _toggle_voice(self):
        """Toggle voice component"""
        if not hasattr(self.bot, 'initialized_components'):
            messagebox.showwarning("Not Available", "Component management not available")
            return
            
        current_status = self.bot.initialized_components.get('voice', False)
        
        if current_status:
            messagebox.showinfo("Voice", "Voice component will remain enabled - disabling is not supported")
        else:
            try:
                messagebox.showinfo("Voice", "Initializing voice component...")
                
                # Attempt to initialize the voice component
                try:
                    # Add src directory to path to help with imports
                    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                    from voice.manager import VoiceManager
                    
                    # Create a basic voice manager with minimal initialization
                    self.bot.voice_manager = VoiceManager(self.bot)
                    self.bot.initialized_components['voice'] = True
                    self.component_status_labels['voice'].config(text="✅ Enabled")
                    messagebox.showinfo("Success", "Voice component enabled successfully")
                    
                except Exception as e:
                    logger.error(f"Error initializing voice manager: {e}")
                    messagebox.showerror("Error", f"Failed to initialize voice manager: {str(e)}")
                    return
                    
            except Exception as e:
                logger.error(f"Error enabling voice: {e}")
                messagebox.showerror("Error", f"Failed to enable voice: {str(e)}")
    
    def _toggle_audio(self):
        """Toggle audio component"""
        if not hasattr(self.bot, 'initialized_components'):
            messagebox.showwarning("Not Available", "Component management not available")
            return
            
        current_status = self.bot.initialized_components.get('audio', False)
        
        if current_status:
            messagebox.showinfo("Audio", "Audio component will remain enabled - disabling is not supported")
        else:
            try:
                messagebox.showinfo("Audio", "Initializing audio component...")
                
                # Attempt to initialize the audio component
                try:
                    # Add src directory to path to help with imports
                    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                    from audio.manager import AudioManager
                    self.bot.audio_manager = AudioManager(self.bot)
                    self.bot.initialized_components['audio'] = True
                    self.component_status_labels['audio'].config(text="✅ Enabled")
                    messagebox.showinfo("Success", "Audio component enabled successfully")
                except Exception as e:
                    logger.error(f"Error initializing audio manager: {e}")
                    messagebox.showerror("Error", f"Failed to initialize audio manager: {str(e)}")
                    return
                    
            except Exception as e:
                logger.error(f"Error enabling audio: {e}")
                messagebox.showerror("Error", f"Failed to enable audio: {str(e)}")
    
    def _apply_voice_settings(self):
        """Apply voice settings"""
        messagebox.showinfo("Voice Settings", "Voice settings will be applied in the next update")
    
    def _apply_audio_settings(self):
        """Apply audio settings"""
        messagebox.showinfo("Audio Settings", "Audio settings will be applied in the next update")
    
    def _setup_logs_tab(self, parent):
        """Set up the logs tab"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Controls
        parent.rowconfigure(1, weight=1)  # Log view
        
        # Controls
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ttk.Button(controls_frame, text="Refresh", command=self._refresh_logs).pack(side="left", padx=5)
        ttk.Button(controls_frame, text="Clear", command=self._clear_logs).pack(side="left", padx=5)
        ttk.Button(controls_frame, text="Save Logs", command=self._save_logs).pack(side="left", padx=5)
        
        # Log level filter
        ttk.Label(controls_frame, text="Level:").pack(side="left", padx=(20, 5))
        level_var = tk.StringVar(value="INFO")
        self.log_level_combo = ttk.Combobox(controls_frame, textvariable=level_var, 
                                            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                                            state="readonly")
        self.log_level_combo.pack(side="left", padx=5)
        self.log_level_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_logs())
        
        # Log view
        log_view = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        log_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Load initial logs
        self._load_logs(log_view)
        self.log_view = log_view
    
    def _load_logs(self, log_view):
        """Load logs into the view"""
        try:
            log_file = "logs/bishop.log"
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    # Get all lines
                    lines = f.readlines()
                    
                    # Filter by level
                    level = self.log_level_combo.get() if hasattr(self, 'log_level_combo') else "INFO"
                    
                    # Mapping of log levels to severity (for filtering)
                    level_map = {
                        "DEBUG": 0,
                        "INFO": 1,
                        "WARNING": 2,
                        "ERROR": 3,
                        "CRITICAL": 4
                    }
                    selected_level = level_map.get(level, 1)  # Default to INFO
                    
                    # Filter lines
                    filtered_lines = []
                    for line in lines:
                        for l, val in level_map.items():
                            if f" - {l} - " in line and val >= selected_level:
                                filtered_lines.append(line)
                                break
                    
                    # Get last 100 filtered lines
                    display_lines = filtered_lines[-100:] if filtered_lines else []
                    
                    # Show in log view
                    if display_lines:
                        log_view.insert(tk.END, "".join(display_lines))
                        log_view.see(tk.END)  # Scroll to end
                    else:
                        log_view.insert(tk.END, f"No log entries found with level {level} or higher")
            else:
                log_view.insert(tk.END, "Log file not found")
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            log_view.insert(tk.END, f"Error loading logs: {str(e)}")
    
    def _refresh_logs(self):
        """Refresh logs"""
        self.log_view.delete(1.0, tk.END)
        self._load_logs(self.log_view)
        
    def _clear_logs(self):
        """Clear log view"""
        self.log_view.delete(1.0, tk.END)
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            # Open file dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Logs",
                defaultextension=".log",
                filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Get log content
            log_content = self.log_view.get(1.0, tk.END)
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
                
            messagebox.showinfo("Success", f"Logs saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving logs: {e}")
            messagebox.showerror("Error", f"Failed to save logs: {str(e)}")
    
    def _setup_buttons(self):
        """Set up bottom buttons (without settings button)"""
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="Refresh", command=self._update_status).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Exit", command=self._on_closing).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    def _update_status(self):
        """Update status information"""
        if not self.running or not self.root:
            return
        
        try:
            # Update connection status
            if self.bot and hasattr(self.bot, 'is_closed') and not self.bot.is_closed():
                self.connection_status.config(text="Connected")
            else:
                self.connection_status.config(text="Disconnected")
            
            # Update servers count
            if self.bot and hasattr(self.bot, 'guilds'):
                self.servers_status.config(text=str(len(self.bot.guilds)))
            
            # Update uptime
            if self.bot and hasattr(self.bot, 'get_uptime'):
                try:
                    self.uptime_status.config(text=self.bot.get_uptime())
                except Exception as e:
                    self.uptime_status.config(text="Error")
                    logger.error(f"Error getting uptime: {e}")
            
            # Update tab-specific information
            self._refresh_servers()
            
            # Schedule next update
            if self.running and self.root:
                self.root.after(1000, self._update_status)
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            if self.running and self.root:
                self.root.after(5000, self._update_status)  # Try again in 5 seconds
    
    def _on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to close the control window?\nThe bot will continue to run."):
            self.running = False
            if self.root:
                self.root.destroy()
            logger.info("Control window closed")


def initialize_control_window(bot):
    """Initialize the control window"""
    try:
        # Check if tkinter is available
        import tkinter
        
        # Create the control window
        window = ControlWindow(bot)
        logger.info("Control window initialized")
        return window
    except ImportError:
        logger.error("Tkinter is not installed - control window cannot be created")
        print("ERROR: Tkinter is not installed - control window cannot be created")
        print("On Windows, reinstall Python with tcl/tk selected during installation")
        print("On Linux, install python3-tk package")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize control window: {e}")
        print(f"ERROR: Failed to initialize control window: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    class DummyBot:
        def __init__(self):
            self.guilds = [
                type('Guild', (), {'id': 123, 'name': 'Test Server 1', 'members': [1, 2, 3], 
                                  'channels': [
                                      type('Channel', (), {'id': 111, 'name': 'general', 'type': 'text'}),
                                      type('Channel', (), {'id': 222, 'name': 'voice-chat', 'type': 'voice'})
                                  ]}),
                type('Guild', (), {'id': 456, 'name': 'Test Server 2', 'members': [1, 2, 3, 4],
                                  'channels': [
                                      type('Channel', (), {'id': 333, 'name': 'text-chat', 'type': 'text'}),
                                      type('Channel', (), {'id': 444, 'name': 'voice-room', 'type': 'voice'})
                                  ]})
            ]
            self.initialized_components = {
                'voice': False,
                'audio': True,
                'database': False
            }
            
            # Dummy voice manager
            self.voice_manager = type('VoiceManager', (), {
                'is_connected': lambda guild_id: guild_id == 123,
                'is_recording': lambda guild_id: False,
                'get_connected_guilds': lambda: [123]
            })
            
            # Dummy audio manager
            self.audio_manager = type('AudioManager', (), {
                'voice_clients': {123: None},
                'now_playing': {},
                'get_sounds_in_category': lambda cat: [
                    type('AudioTrack', (), {'name': f'{cat} Sound 1', 'category': cat}),
                    type('AudioTrack', (), {'name': f'{cat} Sound 2', 'category': cat}),
                    type('AudioTrack', (), {'name': f'{cat} Sound 3', 'category': cat})
                ]
            })
            
            # Event loop for testing asyncio
            self.loop = asyncio.get_event_loop()
        
        def is_closed(self):
            return False
        
        def get_uptime(self):
            return "1h 23m 45s"
            
        def get_guild(self, guild_id):
            for guild in self.guilds:
                if guild.id == guild_id:
                    return guild
            return None
    
    print("Testing control window...")
    window = initialize_control_window(DummyBot())
    
    # Keep main thread alive
    if window:
        while True:
            time.sleep(1)