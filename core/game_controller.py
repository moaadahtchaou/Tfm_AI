#!/usr/bin/env python3
"""
Background Game Controller with AI Integration
"""

import asyncio
import re
import time
import random
import fixedint
import caseus
from caseus import packets
from caseus.packets import serverbound, clientbound

from core.formatter import BotFormatter
from core.window_controller import WindowController
from ai.browser_gemini import BrowserGemini


class BackgroundGameController(caseus.proxies.Proxy):
    """
    Background Game Controller with Browser-Based Gemini AI
    
    Movement Commands:
    $move right 50       - Move bot right 50 pixels
    $jump                - Make bot jump
    $walk right          - Start walking right (continuous)
    $stop                - Stop walking
    $spam jump 5         - Jump 5 times rapidly
    $combo right jump    - Move right then jump
    $chat Hello world!   - Make bot say something
    $status              - Show bot status
    
    AI Commands (Browser-Based):
    $ai What is 2+2?     - Ask Gemini AI via browser
    $ask How are you?    - Alternative AI command
    $aiclose             - Close AI browser
    $aiopen              - Open/restart AI browser
    
    Works with whispers: /w BotName $ai Hello
    """
    
    def __init__(self, config=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.config = config or {}
        self.enabled = True
        
        # Bot control settings
        self.controller_username = self.config.get('controller_username', None)
        self.bot_username = None
        
        # Window controller
        self.window_controller = None
        
        # Bot connection tracking
        self.bot_connection = None
        
        # Browser-based Gemini AI
        ai_config = self.config.get('ai_config', {})
        self.gemini = BrowserGemini(
            browser_type=ai_config.get('browser_type', 'chrome'),
            headless=ai_config.get('headless', False)
        )
        
        # Continuous movement tracking
        self.continuous_movement = None  # 'left', 'right', or None
        self.movement_task = None
        
        # Command patterns
        self._setup_command_patterns()
        
        # Setup packet listeners
        self._setup_listeners()
        
        # Initialize window controller
        self._init_window_controller()
        
        self._log_initialization()
    
    def _setup_command_patterns(self):
        """Setup regex patterns for command parsing"""
        self.move_pattern = re.compile(r'\$move\s+(left|right|up|down)\s*(\d+)?', re.IGNORECASE)
        self.walk_pattern = re.compile(r'\$walk\s+(left|right)', re.IGNORECASE)
        self.spam_pattern = re.compile(r'\$spam\s+(jump|left|right|up|down)\s+(\d+)', re.IGNORECASE)
        self.combo_pattern = re.compile(r'\$combo\s+((?:left|right|up|down|jump|space)\s*)+', re.IGNORECASE)
        self.chat_pattern = re.compile(r'\$chat\s+(.+)', re.IGNORECASE)
        
        # AI command patterns
        self.ai_pattern = re.compile(r'\$(?:ai|ask)\s+(.+)', re.IGNORECASE)
        
        # Window management patterns (simplified)
        self.window_select_pattern = re.compile(r'\$select\s+(.+)', re.IGNORECASE)
        
        self.command_patterns = {
            'jump': re.compile(r'\$jump', re.IGNORECASE),
            'stop': re.compile(r'\$stop', re.IGNORECASE),
            'status': re.compile(r'\$status', re.IGNORECASE),
            'enable': re.compile(r'\$on', re.IGNORECASE),
            'disable': re.compile(r'\$off', re.IGNORECASE),
            'reset': re.compile(r'\$reset', re.IGNORECASE),
            'find_window': re.compile(r'\$find', re.IGNORECASE),
            'list_windows': re.compile(r'\$windows', re.IGNORECASE),
            'ai_close': re.compile(r'\$aiclose', re.IGNORECASE),
            'ai_open': re.compile(r'\$aiopen', re.IGNORECASE),
        }
    
    def _init_window_controller(self):
        """Initialize the window controller"""
        try:
            self.window_controller = WindowController()
            # Give some time for game to start
            asyncio.create_task(self._delayed_window_setup())
        except Exception as e:
            BotFormatter.log(f"Failed to initialize window controller: {e}", "ERROR")
    
    async def _delayed_window_setup(self):
        """Setup window after a delay to let game start"""
        await asyncio.sleep(3)  # Wait 3 seconds
        if self.window_controller:
            self.window_controller.set_bot_window()
    
    def _setup_listeners(self):
        """Setup packet listeners for bot functionality"""
        # Listen for chat messages (room chat)
        self.register_packet_listener(self._on_room_message, clientbound.RoomMessagePacket)
        
        # Try to register whisper listeners with multiple approaches
        self._setup_whisper_listeners()
        
        # Track logins to identify accounts
        try:
            self.register_packet_listener(self._track_login, clientbound.LoginSuccessPacket)
        except Exception as e:
            BotFormatter.log(f"Failed to register login listener: {e}", "ERROR")
    
    def _setup_whisper_listeners(self):
        """Setup whisper packet listeners with fallback methods"""
        whisper_listeners_registered = 0
        whisper_packet_classes = set()  # Track which classes we've already tried
        
        # Method 1: Try standard WhisperPacket
        try:
            if clientbound.WhisperPacket not in whisper_packet_classes:
                self.register_packet_listener(self._on_whisper_message, clientbound.WhisperPacket)
                whisper_packet_classes.add(clientbound.WhisperPacket)
                BotFormatter.log("Registered standard WhisperPacket listener", "SUCCESS")
                whisper_listeners_registered += 1
        except (AttributeError, ImportError):
            BotFormatter.log("Standard WhisperPacket not found", "WARNING")
        except Exception as e:
            BotFormatter.log(f"Failed to register standard WhisperPacket: {e}", "WARNING")
        
        # Method 2: Try TribulleWhisperPacket
        try:
            from caseus.packets.clientbound.tribulle import WhisperPacket as TribulleWhisperPacket
            if TribulleWhisperPacket not in whisper_packet_classes:
                self.register_packet_listener(self._on_whisper_message, TribulleWhisperPacket)
                whisper_packet_classes.add(TribulleWhisperPacket)
                BotFormatter.log("Registered TribulleWhisperPacket listener", "SUCCESS")
                whisper_listeners_registered += 1
        except (AttributeError, ImportError):
            BotFormatter.log("TribulleWhisperPacket not found", "WARNING")
        except Exception as e:
            BotFormatter.log(f"Failed to register TribulleWhisperPacket: {e}", "WARNING")
        
        # Method 3: Register a debug listener for ALL clientbound packets to find whispers
        if whisper_listeners_registered == 0:
            BotFormatter.log("No whisper packets found, registering debug listener for all packets", "WARNING")
            try:
                self.register_packet_listener(self._debug_all_packets, packets.Packet)
            except Exception as e:
                BotFormatter.log(f"Failed to register debug listener: {e}", "ERROR")
    
    def _log_initialization(self):
        """Log initialization messages"""
        BotFormatter.log("Background Game Controller with Browser AI initialized", "BOT")
        BotFormatter.log("Movement Commands:", "INFO")
        BotFormatter.log("  $move right 50 - Move bot right 50 pixels", "INFO")
        BotFormatter.log("  $jump - Make bot jump", "INFO")
        BotFormatter.log("  $walk right - Start continuous walking", "INFO")
        BotFormatter.log("  $stop - Stop continuous movement", "INFO")
        BotFormatter.log("Browser AI Commands:", "AI")
        BotFormatter.log("  $ai What is the weather? - Ask Gemini via browser", "AI")
        BotFormatter.log("  $ask How are you? - Alternative AI command", "AI")
        BotFormatter.log("  $aiopen - Open/restart browser", "AI")
        BotFormatter.log("  $aiclose - Close browser", "AI")
        BotFormatter.log("Window Commands:", "WINDOW")
        BotFormatter.log("  $windows - List all game windows", "WINDOW")
        BotFormatter.log("  $select 1 - Select window 1", "WINDOW")
        BotFormatter.log("  $select 2 - Select window 2", "WINDOW")
        BotFormatter.log("  $select bot - Select window containing 'bot'", "WINDOW")
        BotFormatter.log("Commands work in both ROOM CHAT and WHISPERS!", "SUCCESS")
    
    async def _debug_all_packets(self, source, packet):
        """Debug listener to find whisper packets"""
        packet_type = type(packet).__name__
        
        # Look for packets that might contain whisper data
        if 'whisper' in packet_type.lower() or ('message' in packet_type.lower() and 'room' not in packet_type.lower()):
            BotFormatter.log(f"Found potential whisper packet: {packet_type}", "DEBUG")
            
            # Try to extract whisper-like data
            packet_data = {}
            for attr in ['sender', 'receiver', 'message', 'username', 'target', 'content']:
                if hasattr(packet, attr):
                    value = getattr(packet, attr)
                    packet_data[attr] = value
                    BotFormatter.log(f"  {attr}: {value}", "DEBUG")
            
            # If this looks like a whisper with a command, process it
            message = packet_data.get('message') or packet_data.get('content')
            sender = packet_data.get('sender') or packet_data.get('username')
            
            if message and sender and message.strip().startswith('$'):
                BotFormatter.log(f"Found command in debug packet from {sender}: {message}", "INFO")
                await self._process_command(sender, message, is_whisper=True)
    
    async def _track_login(self, source, packet):
        """Track which connection belongs to which account"""
        username = packet.username
        
        if self.controller_username and username.lower() == self.controller_username.lower():
            source._is_controller_account = True
            source._is_bot_account = False
            BotFormatter.log(f"Controller account connected: {username}", "REMOTE")
        else:
            if self.bot_username is None:
                self.bot_username = username
                source._is_bot_account = True
                source._is_controller_account = False
                self.bot_connection = source  # Store bot connection for chat
                BotFormatter.log(f"Bot account connected: {username}", "BOT")
                
                # Try to find window after bot connects
                if self.window_controller:
                    await asyncio.sleep(1)
                    self.window_controller.set_bot_window()
            else:
                if self.controller_username is None:
                    self.controller_username = username
                source._is_controller_account = True
                source._is_bot_account = False
                BotFormatter.log(f"Controller account connected: {username}", "REMOTE")
    
    async def _on_room_message(self, source, packet):
        """Process room chat messages for bot commands"""
        if not self.enabled or not self.window_controller:
            return
        
        username = packet.username
        message = packet.message
        
        # Only accept commands from the controller (case insensitive)
        if self.controller_username and username.lower() != self.controller_username.lower():
            return
        
        # Process the command
        await self._process_command(username, message, is_whisper=False)
    
    async def _on_whisper_message(self, source, packet):
        """Process whisper messages for bot commands"""
        if not self.enabled:
            return
        
        # Debug: Log all whisper details
        sender = getattr(packet, 'sender', None)
        receiver = getattr(packet, 'receiver', None)  
        message = getattr(packet, 'message', None)
        
        # Try alternative attribute names if the standard ones don't work
        if sender is None:
            sender = getattr(packet, 'username', None)
        if receiver is None:
            receiver = getattr(packet, 'target', None)
        if message is None:
            message = getattr(packet, 'content', None)
        
        if not sender or not receiver or not message:
            BotFormatter.log(f"Invalid whisper packet: sender={sender}, receiver={receiver}, message={message}", "ERROR")
            return
        
        # Check if this whisper is a command to the bot
        is_command_to_bot = self._is_command_to_bot(sender, receiver, message)
        
        if is_command_to_bot:
            BotFormatter.log(f"Processing whisper command from {sender}: {message}", "REMOTE")
            await self._process_command(sender, message, is_whisper=True)
        else:
            BotFormatter.log(f"Ignoring whisper - not a command to bot (Controller: {self.controller_username}, Bot: {self.bot_username})", "DEBUG")
    
    def _is_command_to_bot(self, sender, receiver, message):
        """Check if a whisper is a command to the bot"""
        # Case 1: We know both controller and bot usernames
        if self.controller_username and self.bot_username:
            if sender.lower() == self.controller_username.lower() and receiver.lower() == self.bot_username.lower():
                return True
        
        # Case 2: We know controller but not bot (whisper TO anyone from controller)
        elif self.controller_username and sender.lower() == self.controller_username.lower():
            # Assume any whisper from controller is to the bot
            if not self.bot_username:
                self.bot_username = receiver
            return True
        
        # Case 3: We know bot but not controller (whisper TO bot from anyone)
        elif self.bot_username and receiver.lower() == self.bot_username.lower():
            if not self.controller_username:
                self.controller_username = sender
            return True
        
        # Case 4: We don't know either, learn from any whisper with commands
        elif not self.controller_username and not self.bot_username:
            # Check if message looks like a command
            if message.strip().startswith('$'):
                self.controller_username = sender
                self.bot_username = receiver
                return True
        
        return False
    
    async def _process_command(self, username, message, is_whisper=False):
        """Process a command from either room chat or whisper"""
        command_source = "WHISPER" if is_whisper else "ROOM CHAT"
        
        # Handle AI commands first
        ai_match = self.ai_pattern.match(message)
        if ai_match:
            question = ai_match.group(1)
            BotFormatter.log(f"{command_source} AI command from {username}: {question}", "AI")
            await self._execute_ai_command(username, question)
            return
        
        # Handle move commands
        move_match = self.move_pattern.match(message)
        if move_match:
            direction = move_match.group(1).lower()
            distance = int(move_match.group(2)) if move_match.group(2) else 50
            
            BotFormatter.log(f"{command_source} command from {username}: move {direction} {distance}px", "REMOTE")
            await self._execute_move(username, direction, distance)
            return
        
        # Handle walk commands (continuous movement)
        walk_match = self.walk_pattern.match(message)
        if walk_match:
            direction = walk_match.group(1).lower()
            BotFormatter.log(f"{command_source} command from {username}: walk {direction}", "REMOTE")
            await self._execute_walk(username, direction)
            return
        
        # Handle spam commands
        spam_match = self.spam_pattern.match(message)
        if spam_match:
            action = spam_match.group(1).lower()
            count = int(spam_match.group(2))
            BotFormatter.log(f"{command_source} command from {username}: spam {action} {count}", "REMOTE")
            await self._execute_spam(username, action, count)
            return
        
        # Handle combo commands
        combo_match = self.combo_pattern.match(message)
        if combo_match:
            actions = combo_match.group(1).strip().split()
            BotFormatter.log(f"{command_source} command from {username}: combo {' '.join(actions)}", "REMOTE")
            await self._execute_combo(username, actions)
            return
        
        # Handle chat commands
        chat_match = self.chat_pattern.match(message)
        if chat_match:
            chat_message = chat_match.group(1)
            BotFormatter.log(f"{command_source} command from {username}: chat '{chat_message}'", "REMOTE")
            await self._execute_chat(username, chat_message)
            return
        
        # Handle window switch commands
        window_switch_match = self.window_switch_pattern.match(message)
        if window_switch_match:
            window_index = int(window_switch_match.group(1))
            BotFormatter.log(f"{command_source} command from {username}: switch to window {window_index}", "REMOTE")
            await self._execute_window_switch(username, window_index)
            return
        
        # Handle window select commands
        window_select_match = self.window_select_pattern.match(message)
        if window_select_match:
            search_term = window_select_match.group(1)
            BotFormatter.log(f"{command_source} command from {username}: select window containing '{search_term}'", "REMOTE")
            await self._execute_window_select(username, search_term)
            return
        
        # Handle other commands
        for command_name, pattern in self.command_patterns.items():
            if pattern.match(message):
                BotFormatter.log(f"{command_source} command from {username}: {command_name}", "REMOTE")
                
                # Special handling for list_windows command
                if command_name == "list_windows":
                    await self._execute_list_windows()
                elif command_name == "current_window":
                    await self._execute_current_window()
                else:
                    await self._execute_command(username, command_name)
                return
        
        # Debug: Log unrecognized commands
        if message.strip().startswith('$'):
            BotFormatter.log(f"Unrecognized command: {message}", "DEBUG")