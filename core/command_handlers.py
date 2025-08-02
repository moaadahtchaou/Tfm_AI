#!/usr/bin/env python3
"""
Command execution handlers for the game controller
"""

import asyncio
import time
import random
import re
from core.formatter import BotFormatter


class CommandHandlers:
    """Mixin class for command execution methods"""
    
    async def _execute_ai_command(self, username, question):
        """Execute AI command using browser-based Gemini"""
        try:
            # Send "thinking" message first
            await self._send_bot_message("🤔 Thinking...")
            
            # Add human-like delay before processing
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Get response from browser Gemini
            response = await self.gemini.ask_question(question)
            
            # Smart message splitting for Transformice chat limit (~90 chars)
            max_length = 85  # Leave some margin for emojis
            
            if len(response) <= max_length:
                await self._send_bot_message(f"🤖 {response}")
            else:
                # Smart word-boundary splitting
                chunks = self._split_message_smart(response, max_length - 4)  # -4 for "🤖 " prefix
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        # First chunk gets the robot emoji
                        await self._send_bot_message(f"🤖 {chunk}")
                    else:
                        # Subsequent chunks get continuation indicator
                        await self._send_bot_message(f"   {chunk}")
                    
                    # Human-like delay between messages (2-4 seconds)
                    if i < len(chunks) - 1:  # Don't delay after last chunk
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                    
        except Exception as e:
            BotFormatter.log(f"Error in AI command: {e}", "ERROR")
            await self._send_bot_message(f"❌ AI Error: {str(e)[:50]}...")
    
    def _split_message_smart(self, text, max_length):
        """Split message at word boundaries, preserving sentence structure"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first (., !, ?)
        sentences = re.split(r'([.!?]\s*)', text)
        
        # Rejoin sentence parts
        full_sentences = []
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                full_sentences.append(sentence.strip())
        
        for sentence in full_sentences:
            # If sentence is too long, split by words
            if len(sentence) > max_length:
                words = sentence.split()
                temp_chunk = ""
                
                for word in words:
                    # Check if adding this word would exceed limit
                    test_chunk = f"{temp_chunk} {word}".strip()
                    
                    if len(test_chunk) <= max_length:
                        temp_chunk = test_chunk
                    else:
                        # Save current chunk and start new one
                        if temp_chunk:
                            if current_chunk and len(current_chunk + " " + temp_chunk) <= max_length:
                                current_chunk = f"{current_chunk} {temp_chunk}".strip()
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = temp_chunk
                        else:
                            # Single word is too long, force split
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = ""
                            # Split long word if absolutely necessary
                            if len(word) > max_length:
                                chunks.append(word[:max_length-3] + "...")
                                current_chunk = "..." + word[max_length-3:]
                            else:
                                current_chunk = word
                        
                        temp_chunk = word
                
                # Add remaining temp_chunk
                if temp_chunk:
                    if current_chunk and len(current_chunk + " " + temp_chunk) <= max_length:
                        current_chunk = f"{current_chunk} {temp_chunk}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = temp_chunk
            else:
                # Sentence fits, try to add to current chunk
                if current_chunk and len(current_chunk + " " + sentence) <= max_length:
                    current_chunk = f"{current_chunk} {sentence}".strip()
                else:
                    # Start new chunk
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Ensure no empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return chunks if chunks else [text[:max_length]]
    
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
            BotFormatter.log("=== Bot Status ===", "INFO")
            BotFormatter.log(f"Enabled: {self.enabled}", "INFO")
            BotFormatter.log(f"Bot account: {self.bot_username}", "INFO")
            BotFormatter.log(f"Controller: {self.controller_username}", "INFO")
            BotFormatter.log(f"Window valid: {self.window_controller.is_window_valid() if self.window_controller else False}", "INFO")
            BotFormatter.log(f"Continuous movement: {self.continuous_movement}", "INFO")
            BotFormatter.log(f"Browser AI: {'Initialized' if self.gemini.is_initialized else 'Not initialized'}", "INFO")
            BotFormatter.log("Commands work in ROOM CHAT and WHISPERS", "INFO")
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
            BotFormatter.log("Bot enabled", "SUCCESS")
        
        elif command == "disable":
            self.enabled = False
            BotFormatter.log("Bot disabled", "WARNING")
        
        elif command == "reset":
            if self.movement_task:
                self.movement_task.cancel()
                self.movement_task = None
            self.continuous_movement = None
            BotFormatter.log("Bot reset", "SUCCESS")
        
        elif command == "find_window":
            if self.window_controller:
                def find():
                    self.window_controller.set_bot_window()
                await asyncio.get_event_loop().run_in_executor(None, find)
        
        elif command == "ai_close":
            self.gemini.close()
            await self._send_bot_message("🔴 Browser closed")
        
        elif command == "ai_open":
            success = await self.gemini.initialize()
            if success:
                await self._send_bot_message("🟢 Browser ready!")
            else:
                await self._send_bot_message("❌ Browser failed to start")

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
                await self._send_bot_message(f"✅ Switched to window {window_index}")
            else:
                await self._send_bot_message(f"❌ Failed to switch to window {window_index}")
            return
            
        except ValueError:
            # Not a number, treat as title search
            pass
        
        def select_window():
            return self.window_controller.set_bot_window(window_title_contains=search_term)
        
        try:
            success = await asyncio.get_event_loop().run_in_executor(None, select_window)
            if success:
                await self._send_bot_message(f"✅ Selected window containing '{search_term}'")
            else:
                await self._send_bot_message(f"❌ No window found containing '{search_term}'")
        except Exception as e:
            BotFormatter.log(f"Window select failed: {e}", "ERROR")
            await self._send_bot_message("❌ Window select error")
    
    async def _execute_list_windows(self):
        """List all available windows"""
        BotFormatter.log("Executing list_windows command", "DEBUG")
        
        if not self.window_controller:
            BotFormatter.log("Window controller not available", "ERROR")
            await self._send_bot_message("❌ Window controller not available")
            return
        
        def get_windows():
            BotFormatter.log("Getting windows from controller", "DEBUG")
            return self.window_controller.list_windows()
        
        try:
            BotFormatter.log("Running window detection", "DEBUG")
            windows = await asyncio.get_event_loop().run_in_executor(None, get_windows)
            BotFormatter.log(f"Got {len(windows) if windows else 0} windows from detection", "DEBUG")
            
            if not windows:
                await self._send_bot_message("❌ No Transformice windows found")
                await asyncio.sleep(1)
                await self._send_bot_message("💡 Make sure Transformice is running")
                await asyncio.sleep(1) 
                await self._send_bot_message("🔍 Try: $debug for detailed scan")
                return
            
            # Send window list in chat
            await self._send_bot_message(f"🪟 Found {len(windows)} windows:")
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
            await self._send_bot_message("❌ Error listing windows")