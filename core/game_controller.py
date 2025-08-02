#!/usr/bin/env python3
"""
Enhanced Game Controller with Advanced AI System
REPLACE: core/game_controller.py
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
from ai.advanced_browser_gemini import AdvancedBrowserGemini


class BackgroundGameController(caseus.proxies.Proxy):
    """
    Enhanced Background Game Controller with Advanced AI System
    
    Basic Commands:
    $move right 50       - Move bot right 50 pixels
    $jump                - Make bot jump
    $walk right          - Start walking right (continuous)
    $stop                - Stop walking
    $spam jump 5         - Jump 5 times rapidly
    $combo right jump    - Move right then jump
    $chat Hello world!   - Make bot say something
    $status              - Show bot status
    
    Advanced AI Commands:
    $newai --darija --anime                    - Create Darija anime AI
    $newai --french --gaming --name "GameBot"  - Create French gaming AI
    $newai --arabic --tech --custom "Expert"   - Create Arabic tech expert
    $switchai darija_anime                     - Switch to specific AI
    $listai                                    - List all AI personalities
    $ai Hello!                                 - Chat with current AI
    
    Available Languages: --darija, --arabic, --french, --english
    Available Topics: --anime, --gaming, --casual, --tech, --sports
    
    Window Commands:
    $windows             - List all game windows
    $select 1            - Select window by index
    $select bot          - Select window containing 'bot'
    
    Works with whispers: /w BotName $newai --darija --anime
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
        
        # Advanced AI system instead of simple browser
        ai_config = self.config.get('ai_config', {})
        self.advanced_gemini = AdvancedBrowserGemini(
            browser_type=ai_config.get('browser_type', 'chrome'),
            headless=ai_config.get('headless', False)
        )
        
        # Keep the simple gemini for backward compatibility
        self.gemini = self.advanced_gemini  # Alias for compatibility
        
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
        
        # Enhanced AI command patterns
        self.ai_pattern = re.compile(r'\$(?:ai|ask)\s+(.+)', re.IGNORECASE)
        self.newai_pattern = re.compile(r'\$newai\s+(.+)', re.IGNORECASE)
        self.switchai_pattern = re.compile(r'\$switchai\s+(\w+)', re.IGNORECASE)
        self.listai_pattern = re.compile(r'\$listai', re.IGNORECASE)
        
        # Window management patterns
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
        whisper_packet_classes = set()
        
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
        BotFormatter.log("Enhanced Game Controller with Advanced AI initialized", "BOT")
        BotFormatter.log("Movement Commands:", "INFO")
        BotFormatter.log("  $move right 50 - Move bot right 50 pixels", "INFO")
        BotFormatter.log("  $jump - Make bot jump", "INFO")
        BotFormatter.log("  $walk right - Start continuous walking", "INFO")
        BotFormatter.log("  $stop - Stop continuous movement", "INFO")
        BotFormatter.log("Advanced AI Commands:", "AI")
        BotFormatter.log("  $newai --darija --anime - Create Darija anime AI", "AI")
        BotFormatter.log("  $newai --french --gaming --name 'GameBot' - Named French gaming AI", "AI")
        BotFormatter.log("  $switchai darija_anime - Switch to specific AI", "AI")
        BotFormatter.log("  $listai - List all AI personalities", "AI")
        BotFormatter.log("  $ai Hello! - Chat with current AI", "AI")
        BotFormatter.log("Window Commands:", "WINDOW")
        BotFormatter.log("  $windows - List all game windows", "WINDOW")
        BotFormatter.log("  $select 1 - Select window 1", "WINDOW")
        BotFormatter.log("  $select bot - Select window containing 'bot'", "WINDOW")
        BotFormatter.log("Languages: darija, arabic, french, english", "AI")
        BotFormatter.log("Topics: anime, gaming, casual, tech, sports", "AI")
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
        """Process a command from either room chat or whisper with enhanced AI support"""
        command_source = "WHISPER" if is_whisper else "ROOM CHAT"
        
        # Handle NEW AI creation commands
        newai_match = self.newai_pattern.match(message)
        if newai_match:
            ai_args = newai_match.group(1)
            BotFormatter.log(f"{command_source} NEW AI command from {username}: {ai_args}", "AI")
            await self._execute_newai_command(username, ai_args)
            return
        
        # Handle AI SWITCH commands
        switchai_match = self.switchai_pattern.match(message)
        if switchai_match:
            ai_name = switchai_match.group(1)
            BotFormatter.log(f"{command_source} SWITCH AI command from {username}: {ai_name}", "AI")
            await self._execute_switchai_command(username, ai_name)
            return
        
        # Handle LIST AI commands
        listai_match = self.listai_pattern.match(message)
        if listai_match:
            BotFormatter.log(f"{command_source} LIST AI command from {username}", "AI")
            await self._execute_listai_command(username)
            return
        
        # Handle regular AI commands (using current personality)
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
                else:
                    await self._execute_command(username, command_name)
                return
        
        # Debug: Log unrecognized commands
        if message.strip().startswith('$'):
            BotFormatter.log(f"Unrecognized command: {message}", "DEBUG")

    # Enhanced AI command execution methods
    async def _execute_newai_command(self, username, ai_args):
        """Execute new AI creation command"""
        try:
            # Send "creating" message first
            await self._send_bot_message("Creating new AI personality...")
            
            # Create the new AI
            result = await self.advanced_gemini.create_new_ai(ai_args)
            
            # Send result
            await self._send_bot_message(result)
            
            # Show usage instructions only if successful
            if result == "Done new personality":
                await asyncio.sleep(0.3)
            
        except Exception as e:
            BotFormatter.log(f"Error in newai command: {e}", "ERROR")
            await self._send_bot_message(f"Error creating AI: {str(e)[:50]}...")
    
    async def _execute_switchai_command(self, username, ai_name):
        """Execute AI switch command"""
        try:
            # Send "switching" message first
            await self._send_bot_message(f"Switching to AI: {ai_name}...")
            
            # Switch to the AI
            result = await self.advanced_gemini.switch_to_ai(ai_name)
            
            # Send result
            await self._send_bot_message(result)
            
        except Exception as e:
            BotFormatter.log(f"Error in switchai command: {e}", "ERROR")
            await self._send_bot_message(f"Error switching AI: {str(e)[:50]}...")
    
    async def _execute_listai_command(self, username):
        """Execute list AI command"""
        try:
            # Get the list of personalities
            ai_list = self.advanced_gemini.list_personalities()
            
            # Split into chunks for chat
            lines = ai_list.split('\n')
            
            for line in lines:
                if line.strip():
                    # Truncate long lines
                    if len(line) > 85:
                        line = line[:82] + "..."
                    await self._send_bot_message(line)
                    await asyncio.sleep(0.5)  # Delay between messages
                    
        except Exception as e:
            BotFormatter.log(f"Error in listai command: {e}", "ERROR")
            await self._send_bot_message(f"Error listing AIs: {str(e)[:50]}...")
    
    async def _execute_ai_command(self, username, question):
        """Execute AI command using the current personality"""
        try:
            # Send "thinking" message first
            await self._send_bot_message("Thinking...")
            
            # Add human-like delay before processing
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Get response from the current AI personality
            response = await self.advanced_gemini.ask_question(question)
            
            # Smart message splitting for Transformice chat limit (~90 chars)
            max_length = 85  # Leave some margin for emojis
            
            if len(response) <= max_length:
                await self._send_bot_message(f"{response}")
            else:
                # Smart word-boundary splitting
                chunks = self._split_message_smart(response, max_length - 4)  # -4 for "🤖 " prefix
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        # First chunk gets the robot emoji
                        await self._send_bot_message(f"{chunk}")
                    else:
                        # Subsequent chunks get continuation indicator
                        await self._send_bot_message(f"   {chunk}")
                    
                    # Human-like delay between messages (2-4 seconds)
                    if i < len(chunks) - 1:  # Don't delay after last chunk
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                    
        except Exception as e:
            BotFormatter.log(f"Error in AI command: {e}", "ERROR")
            await self._send_bot_message(f" AI Error: {str(e)[:50]}...")

    def _split_message_smart(self, text, max_length):
        """Split message at word boundaries, preserving all content"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        words = text.split()  # Split into words
        current_chunk = ""
        
        for word in words:
            # Check if adding this word would exceed the limit
            test_chunk = f"{current_chunk} {word}".strip() if current_chunk else word
            
            if len(test_chunk) <= max_length:
                # Word fits, add it to current chunk
                current_chunk = test_chunk
            else:
                # Word doesn't fit
                if current_chunk:
                    # Save current chunk and start new one with this word
                    chunks.append(current_chunk)
                    current_chunk = word
                else:
                    # Single word is too long, we have to split it
                    if len(word) > max_length:
                        # Split long word
                        chunks.append(word[:max_length-3] + "...")
                        current_chunk = "..." + word[max_length-3:]
                    else:
                        current_chunk = word
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
        
        # Ensure we have at least one chunk
        if not chunks:
            chunks = [text[:max_length]]
        
        return chunks
    
    async def _send_bot_message(self, message):
        """Send a message from the bot to the game chat"""
        await self._execute_chat("AI", message)
    
    async def _execute_move(self, username, direction, distance):
        """Execute movement command"""
        if not self.window_controller.is_window_valid():
            BotFormatter.log("Bot window is not valid! Use $find", "ERROR")
            return
        
        def move():
            self.window_controller.move_character(direction, distance)
        
        await asyncio.get_event_loop().run_in_executor(None, move)
    
    async def _execute_walk(self, username, direction):
        """Execute continuous walking"""
        # Stop current walking
        if self.movement_task:
            self.movement_task.cancel()
            self.movement_task = None
        
        # Start new walking
        self.continuous_movement = direction
        self.movement_task = asyncio.create_task(self._continuous_walk(direction))
    
    async def _continuous_walk(self, direction):
        """Continuous walking task"""
        try:
            while self.continuous_movement == direction:
                if self.window_controller.is_window_valid():
                    def walk_step():
                        self.window_controller.send_key_to_window(direction, 0.1)
                    
                    await asyncio.get_event_loop().run_in_executor(None, walk_step)
                    await asyncio.sleep(0.05)  # Small delay between steps
                else:
                    break
        except asyncio.CancelledError:
            BotFormatter.log(f"Stopped walking {direction}", "INFO")
    
    async def _execute_spam(self, username, action, count):
        """Execute spam command"""
        if not self.window_controller.is_window_valid():
            BotFormatter.log("Bot window is not valid! Use $find", "ERROR")
            return
        
        def spam():
            for i in range(count):
                if action == "jump":
                    self.window_controller.jump()
                else:
                    self.window_controller.send_key_to_window(action, 0.1)
                time.sleep(0.1)
        
        await asyncio.get_event_loop().run_in_executor(None, spam)
        BotFormatter.log(f"Completed spam {action} {count} times", "SUCCESS")
    
    async def _execute_combo(self, username, actions):
        """Execute combo command"""
        if not self.window_controller.is_window_valid():
            BotFormatter.log("Bot window is not valid! Use $find", "ERROR")
            return
        
        def combo():
            for action in actions:
                action = action.lower()
                if action == "jump":
                    self.window_controller.jump()
                elif action in ['left', 'right', 'up', 'down', 'space']:
                    self.window_controller.send_key_to_window(action, 0.2)
                time.sleep(0.2)  # Delay between combo actions
        
        await asyncio.get_event_loop().run_in_executor(None, combo)
        BotFormatter.log(f"Completed combo: {' '.join(actions)}", "SUCCESS")
    
    async def _execute_chat(self, username, message):
        """Execute chat command using Windows API only"""
        # Convert message to string and ensure it's not empty
        message = str(message).strip()
        if not message:
            return
            
        # Use Windows API method only
        if self.window_controller and self.window_controller.is_window_valid():
            def send_chat():
                success = self.window_controller.send_chat_to_window(message)
                return success
            
            try:
                success = await asyncio.get_event_loop().run_in_executor(None, send_chat)
                if success:
                    BotFormatter.log(f"Bot sent message: {message}", "SUCCESS")
                else:
                    BotFormatter.log("Chat method failed", "ERROR")
            except Exception as e:
                BotFormatter.log(f"Chat failed: {e}", "ERROR")
        else:
            BotFormatter.log("Bot window not valid - cannot send chat!", "ERROR")
    
    async def _execute_command(self, username, command):
        """Execute other commands"""
        if command == "jump":
            if self.window_controller.is_window_valid():
                def jump():
                    self.window_controller.jump()
                await asyncio.get_event_loop().run_in_executor(None, jump)
                BotFormatter.log("Jump executed", "SUCCESS")
            else:
                BotFormatter.log("Bot window is not valid!", "ERROR")
        
        elif command == "stop":
            if self.movement_task:
                self.movement_task.cancel()
                self.movement_task = None
            self.continuous_movement = None
            BotFormatter.log("All movement stopped", "SUCCESS")
        
        elif command == "status":
            BotFormatter.log("=== Enhanced Bot Status ===", "INFO")
            BotFormatter.log(f"Enabled: {self.enabled}", "INFO")
            BotFormatter.log(f"Bot account: {self.bot_username}", "INFO")
            BotFormatter.log(f"Controller: {self.controller_username}", "INFO")
            BotFormatter.log(f"Window valid: {self.window_controller.is_window_valid() if self.window_controller else False}", "INFO")
            BotFormatter.log(f"Continuous movement: {self.continuous_movement}", "INFO")
            BotFormatter.log(f"Advanced AI: {'Initialized' if self.advanced_gemini.is_initialized else 'Not initialized'}", "INFO")
            BotFormatter.log(f"Current AI: {self.advanced_gemini.current_personality.name if self.advanced_gemini.current_personality else 'None'}", "INFO")
            BotFormatter.log(f"Total AI personalities: {len(self.advanced_gemini.personalities)}", "INFO")
            BotFormatter.log("Enhanced commands: $newai, $switchai, $listai, $ai", "INFO")
            if self.window_controller:
                BotFormatter.log(f"Bot window handle: {self.window_controller.bot_window_handle}", "INFO")
                # Quick window count check
                try:
                    window_count = len(self.window_controller.find_transformice_windows())
                    BotFormatter.log(f"Available windows: {window_count}", "INFO")
                except Exception as e:
                    BotFormatter.log(f"Window detection error: {e}", "ERROR")
        
        elif command == "enable":
            self.enabled = True
            BotFormatter.log("Enhanced bot enabled", "SUCCESS")
        
        elif command == "disable":
            self.enabled = False
            BotFormatter.log("Enhanced bot disabled", "WARNING")
        
        elif command == "reset":
            if self.movement_task:
                self.movement_task.cancel()
                self.movement_task = None
            self.continuous_movement = None
            BotFormatter.log("Enhanced bot reset", "SUCCESS")
        
        elif command == "find_window":
            if self.window_controller:
                def find():
                    self.window_controller.set_bot_window()
                await asyncio.get_event_loop().run_in_executor(None, find)
        
        elif command == "ai_close":
            self.advanced_gemini.close()
            await self._send_bot_message("Advanced browser closed")
        
        elif command == "ai_open":
            success = await self.advanced_gemini.initialize()
            if success:
                await self._send_bot_message("Advanced browser ready!")
            else:
                await self._send_bot_message("Advanced browser failed to start")

    async def _execute_window_select(self, username, search_term):
        """Execute window select by title or index command"""
        if not self.window_controller:
            BotFormatter.log("Window controller not available!", "ERROR")
            return
        
        # Check if search_term is a number (index)
        try:
            window_index = int(search_term)
            # If it's a number, treat it as window index
            BotFormatter.log(f"Selecting window by index: {window_index}", "DEBUG")
            
            def switch_window():
                return self.window_controller.switch_to_window(window_index)
            
            success = await asyncio.get_event_loop().run_in_executor(None, switch_window)
            if success:
                await self._send_bot_message(f"Switched to window {window_index}")
            else:
                await self._send_bot_message(f"Failed to switch to window {window_index}")
            return
            
        except ValueError:
            # Not a number, treat as title search
            pass
        
        def select_window():
            return self.window_controller.set_bot_window(window_title_contains=search_term)
        
        try:
            success = await asyncio.get_event_loop().run_in_executor(None, select_window)
            if success:
                await self._send_bot_message(f"Selected window containing '{search_term}'")
            else:
                await self._send_bot_message(f"No window found containing '{search_term}'")
        except Exception as e:
            BotFormatter.log(f"Window select failed: {e}", "ERROR")
            await self._send_bot_message("Window select error")
    
    async def _execute_list_windows(self):
        """List all available windows"""
        BotFormatter.log("Executing list_windows command", "DEBUG")
        
        if not self.window_controller:
            BotFormatter.log("Window controller not available", "ERROR")
            await self._send_bot_message("Window controller not available")
            return
        
        def get_windows():
            BotFormatter.log("Getting windows from controller", "DEBUG")
            return self.window_controller.list_windows()
        
        try:
            BotFormatter.log("Running window detection", "DEBUG")
            windows = await asyncio.get_event_loop().run_in_executor(None, get_windows)
            BotFormatter.log(f"Got {len(windows) if windows else 0} windows from detection", "DEBUG")
            
            if not windows:
                await self._send_bot_message("No Transformice windows found")
                await asyncio.sleep(1)
                await self._send_bot_message("Make sure Transformice is running")
                await asyncio.sleep(1) 
                await self._send_bot_message("Try: $find for window detection")
                return
            
            # Send window list in chat
            await self._send_bot_message(f"Found {len(windows)} windows:")
            await asyncio.sleep(1)  # Delay between messages
            
            for window in windows:
                status = "👈 CURRENT" if window['is_current'] else ""
                # Truncate long titles
                title = window['title']
                if len(title) > 30:
                    title = title[:27] + "..."
                
                message = f"{window['index']}: {title} {status}"
                await self._send_bot_message(message)
                await asyncio.sleep(0.5)  # Delay between window listings
                
        except Exception as e:
            BotFormatter.log(f"List windows failed: {e}", "ERROR")
            import traceback
            BotFormatter.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
            await self._send_bot_message("Error listing windows")
    
    async def shutdown(self):
        """Shutdown the bot and clean up resources"""
        try:
            BotFormatter.log("Shutting down Enhanced Game Controller...", "INFO")
            
            # Stop any running movement tasks
            if self.movement_task:
                self.movement_task.cancel()
                try:
                    await self.movement_task
                except asyncio.CancelledError:
                    pass
                self.movement_task = None
            
            # Close the browser
            if hasattr(self, 'advanced_gemini') and self.advanced_gemini:
                self.advanced_gemini.close()
            
            # Close the window controller
            if hasattr(self, 'window_controller') and self.window_controller:
                # Window controller doesn't need explicit cleanup
                pass
            
            BotFormatter.log("Enhanced Game Controller shutdown complete", "INFO")
            
        except Exception as e:
            BotFormatter.log(f"Error during shutdown: {e}", "ERROR")