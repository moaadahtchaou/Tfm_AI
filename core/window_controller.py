#!/usr/bin/env python3
"""
Windows API controller for game window interaction
"""

import time
import random
from core.formatter import BotFormatter

# Windows API imports for background input
try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import win32clipboard
    import ctypes
    from ctypes import wintypes
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False


class WindowController:
    """Controls a specific window using Windows API"""
    
    def __init__(self):
        if not WINDOWS_API_AVAILABLE:
            raise Exception("Windows API not available. Install pywin32: pip install pywin32")
        
        self.bot_window_handle = None
        self.bot_process_id = None
        
        # Virtual key codes
        self.VK_LEFT = 0x25
        self.VK_UP = 0x26
        self.VK_RIGHT = 0x27
        self.VK_DOWN = 0x28
        self.VK_SPACE = 0x20
        self.VK_RETURN = 0x0D
        
        # Key mapping
        self.key_map = {
            'left': self.VK_LEFT,
            'right': self.VK_RIGHT,
            'up': self.VK_UP,
            'down': self.VK_DOWN,
            'space': self.VK_SPACE,
            'enter': self.VK_RETURN,
        }
    
    def find_transformice_windows(self):
        """Find all Transformice windows"""
        windows = []
        
        def enum_windows_callback(hwnd, lParam):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                
                # Debug: Log all visible windows for troubleshooting
                BotFormatter.log(f"Found window: '{window_title}'", "DEBUG")
                
                # Check for various Transformice window titles
                title_lower = window_title.lower()
                if (
                    "transformice" in title_lower or 
                    "adobe flash player" in title_lower or
                    "flash player" in title_lower or
                    title_lower.startswith("transformice") or
                    "tfm" in title_lower
                ):
                    windows.append((hwnd, window_title))
                    BotFormatter.log(f"Matched Transformice window: '{window_title}'", "WINDOW")
            return True
        
        BotFormatter.log("Scanning for Transformice windows...", "DEBUG")
        win32gui.EnumWindows(enum_windows_callback, None)
        BotFormatter.log(f"Found {len(windows)} Transformice windows total", "DEBUG")
        
        return windows
    
    def set_bot_window(self, window_title_contains="", window_index=None):
        """Set which window is the bot window"""
        windows = self.find_transformice_windows()
        
        if not windows:
            BotFormatter.log("No Transformice windows found!", "ERROR")
            return False
        
        BotFormatter.log("Found Transformice windows:", "WINDOW")
        for i, (hwnd, title) in enumerate(windows):
            BotFormatter.log(f"  {i+1}: {title} (Handle: {hwnd})", "WINDOW")
        
        # Select window based on criteria
        selected_window = None
        
        if window_index is not None:
            # Select by index (1-based)
            if 1 <= window_index <= len(windows):
                selected_window = windows[window_index - 1]
                BotFormatter.log(f"Selected window {window_index} by index", "WINDOW")
            else:
                BotFormatter.log(f"Invalid window index {window_index}. Available: 1-{len(windows)}", "ERROR")
                return False
        elif window_title_contains:
            # Select by title content
            for hwnd, title in windows:
                if window_title_contains.lower() in title.lower():
                    selected_window = (hwnd, title)
                    BotFormatter.log(f"Selected window by title containing: {window_title_contains}", "WINDOW")
                    break
            if not selected_window:
                BotFormatter.log(f"No window found containing: {window_title_contains}", "ERROR")
                return False
        else:
            # Default: use first window
            selected_window = windows[0]
            BotFormatter.log("Selected first window as default", "WINDOW")
        
        if selected_window:
            self.bot_window_handle, window_title = selected_window
            BotFormatter.log(f"Bot window set to: {window_title}", "SUCCESS")
            
            # Get process ID
            _, self.bot_process_id = win32process.GetWindowThreadProcessId(self.bot_window_handle)
            BotFormatter.log(f"Bot process ID: {self.bot_process_id}", "WINDOW")
            return True
        
        return False
    
    def list_windows(self):
        """List all available Transformice windows"""
        windows = self.find_transformice_windows()
        
        if not windows:
            BotFormatter.log("No Transformice windows found!", "WINDOW")
            return []
        
        BotFormatter.log("Available Transformice windows:", "WINDOW")
        window_info = []
        
        for i, (hwnd, title) in enumerate(windows):
            is_current = hwnd == self.bot_window_handle
            status = " (CURRENT)" if is_current else ""
            BotFormatter.log(f"  {i+1}: {title}{status}", "WINDOW")
            window_info.append({
                'index': i + 1,
                'handle': hwnd,
                'title': title,
                'is_current': is_current
            })
        
        return window_info
    
    def switch_to_window(self, window_index):
        """Switch to a specific window by index"""
        return self.set_bot_window(window_index=window_index)
    
    def switch_to_window_by_handle(self, target_handle):
        """Switch to a specific window by handle"""
        windows = self.find_transformice_windows()
        
        for hwnd, title in windows:
            if hwnd == target_handle:
                self.bot_window_handle = hwnd
                self.bot_process_id = win32process.GetWindowThreadProcessId(hwnd)[1]
                BotFormatter.log(f"Switched to window: {title} (Handle: {hwnd})", "SUCCESS")
                return True
        
        BotFormatter.log(f"Window handle {target_handle} not found", "ERROR")
        return False
    
    def get_current_window_info(self):
        """Get information about the current bot window"""
        if not self.bot_window_handle:
            return None
        
        try:
            title = win32gui.GetWindowText(self.bot_window_handle)
            is_valid = win32gui.IsWindow(self.bot_window_handle)
            return {
                'handle': self.bot_window_handle,
                'title': title,
                'process_id': self.bot_process_id,
                'is_valid': is_valid
            }
        except:
            return None
    
    def send_key_to_window(self, key, duration=0.1):
        """Send a key press to the bot window (works without focus)"""
        if not self.bot_window_handle:
            BotFormatter.log("No bot window set!", "ERROR")
            return False
        
        if key not in self.key_map:
            BotFormatter.log(f"Unknown key: {key}", "ERROR")
            return False
        
        vk_code = self.key_map[key]
        
        try:
            # Send WM_KEYDOWN message
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYDOWN, vk_code, 0)
            
            # Hold the key for specified duration
            time.sleep(duration)
            
            # Send WM_KEYUP message
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYUP, vk_code, 0)
            
            BotFormatter.log(f"Sent key '{key}' to bot window (duration: {duration}s)", "INPUT")
            return True
            
        except Exception as e:
            BotFormatter.log(f"Failed to send key '{key}': {e}", "ERROR")
            return False
    
    def send_chat_to_window(self, message):
        """Send chat message using Windows API with human-like typing"""
        if not self.bot_window_handle:
            return False
        
        try:
            # Press Enter to open chat
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYDOWN, self.VK_RETURN, 0)
            time.sleep(0.1)
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYUP, self.VK_RETURN, 0)
            
            # Wait for chat box to open (human-like delay)
            time.sleep(random.uniform(0.1, 0.2))
            
            # Type each character with human-like speed and pauses
            for i, char in enumerate(message):
                if char == ' ':
                    # Send space key
                    win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYDOWN, self.VK_SPACE, 0)
                    time.sleep(random.uniform(0.01, 0.02))
                    win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYUP, self.VK_SPACE, 0)
                else:
                    # Send character
                    win32gui.PostMessage(self.bot_window_handle, win32con.WM_CHAR, ord(char), 0)
                
                # Human-like typing delays
                if i % 15 == 14:  # Pause every 15 characters (like thinking)
                    time.sleep(random.uniform(0.1, 0.3))
                elif i % 8 == 7:  # Small pause every 8 characters
                    time.sleep(random.uniform(0.1, 0.2))
                elif char in '.,!?':  # Pause after punctuation
                    time.sleep(random.uniform(0.15, 0.3))
                elif char == ' ':  # Pause after spaces (between words)
                    time.sleep(random.uniform(0.08, 0.15))
                else:
                    # Normal typing speed: 40-80 WPM (converted to character delay)
                    # Average human types 1-3 characters per second
                    time.sleep(random.uniform(0.05, 0.12))
                
                # Occasional longer pauses (like human hesitation)
                if random.random() < 0.1:  # 10% chance
                    time.sleep(random.uniform(0.1, 0.3))
            
            # Wait before sending (like reviewing the message)
            time.sleep(random.uniform(0.1, 0.3))
            
            # Press Enter to send the message
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYDOWN, self.VK_RETURN, 0)
            time.sleep(0.05)
            win32gui.PostMessage(self.bot_window_handle, win32con.WM_KEYUP, self.VK_RETURN, 0)
            
            return True
            
        except Exception as e:
            return False
    
    def move_character(self, direction, distance_pixels=50):
        """Move character in a direction for a calculated time"""
        # Estimate: ~100 pixels per second movement
        movement_speed = 100  # pixels per second
        duration = max(distance_pixels / movement_speed, 0.1)
        
        direction_map = {
            'left': 'left',
            'right': 'right',
            'up': 'up',
            'down': 'down'
        }
        
        if direction in direction_map:
            key = direction_map[direction]
            BotFormatter.log(f"Moving {direction} for {distance_pixels} pixels ({duration:.2f}s)", "INPUT")
            return self.send_key_to_window(key, duration)
        
        return False
    
    def jump(self):
        """Make character jump"""
        return self.send_key_to_window('up', 0.2)
    
    def is_window_valid(self):
        """Check if the bot window is still valid"""
        if not self.bot_window_handle:
            return False
        
        try:
            return win32gui.IsWindow(self.bot_window_handle)
        except:
            return False