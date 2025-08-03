#!/usr/bin/env python3
"""
Reset Window Player Module
Handles closing and reopening Transformice game windows with auto-login
"""

import asyncio
import subprocess
import psutil
import os
import time
from core.formatter import BotFormatter

# Windows API imports
try:
    import win32gui
    import win32con
    import win32process
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False


class ResetWindowPlayer:
    """Handles resetting (closing and reopening) game windows"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.window_controller = None
        
        # Virtual key codes
        self.VK_RETURN = 0x0D
        self.VK_TAB = 0x09
        self.VK_CTRL = 0x11
        self.VK_A = 0x41
    
    def set_window_controller(self, window_controller):
        """Set the window controller reference"""
        self.window_controller = window_controller
    
    async def reset_player(self, send_message_callback=None):
        """
        Main reset player function
        
        Args:
            send_message_callback: Function to send status messages to chat
        """
        if not WINDOWS_API_AVAILABLE:
            await self._send_status("❌ Windows API not available", send_message_callback)
            return False
        
        try:
            await self._send_status("🔄 Restarting game...", send_message_callback)
            
            # Step 1: Close the bot's game window
            BotFormatter.log("Step 1: Closing bot's game window", "INFO")
            success = await self._close_bot_game_window()
            if success:
                await self._send_status("✅ Game window closed", send_message_callback)
            else:
                await self._send_status("⚠️ Game window may still be open", send_message_callback)
            
            await asyncio.sleep(2)
            
            # Step 2: Open new game window
            BotFormatter.log("Step 2: Opening new game window", "INFO")
            await self._send_status("🚀 Opening new game...", send_message_callback)
            
            success = await self._open_new_game_window()
            if not success:
                await self._send_status("❌ Failed to open new game", send_message_callback)
                return False
            
            # Step 3: Wait for game to load (7 seconds as requested)
            BotFormatter.log("Step 3: Waiting 7 seconds for game to load", "INFO")
            await self._send_status("⏳ Waiting for game to load...", send_message_callback)
            await asyncio.sleep(7)
            
            # Step 4: Enter login credentials
            BotFormatter.log("Step 4: Entering login credentials", "INFO")
            await self._send_status("🔐 Entering login...", send_message_callback)
            
            success = await self._enter_login_credentials()
            if success:
                await self._send_status("✅ Login completed! Reconnecting...", send_message_callback)
                
                # Step 5: Reset window controller to find the new window
                await asyncio.sleep(3)
                await self._update_window_controller()
                BotFormatter.log("Reset player process completed successfully", "SUCCESS")
                return True
            else:
                await self._send_status("⚠️ Login may need manual completion", send_message_callback)
                return False
            
        except Exception as e:
            BotFormatter.log(f"Error in reset player: {e}", "ERROR")
            await self._send_status(f"❌ Reset failed: {str(e)[:30]}...", send_message_callback)
            return False
    
    async def _send_status(self, message, callback):
        """Send status message if callback is provided"""
        if callback:
            try:
                await callback(message)
            except Exception as e:
                BotFormatter.log(f"Failed to send status message: {e}", "WARNING")
        BotFormatter.log(message, "INFO")
    
    async def _close_bot_game_window(self):
        """Close the bot's game window"""
        try:
            # Method 1: Close specific window if we have a handle
            if (self.window_controller and 
                hasattr(self.window_controller, 'bot_window_handle') and 
                self.window_controller.bot_window_handle):
                
                try:
                    handle = self.window_controller.bot_window_handle
                    BotFormatter.log(f"Closing specific window with handle: {handle}", "DEBUG")
                    
                    # Send WM_CLOSE message
                    win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
                    await asyncio.sleep(2)
                    
                    # Check if window is closed
                    if not win32gui.IsWindow(handle):
                        BotFormatter.log("Bot window closed successfully", "SUCCESS")
                        return True
                    else:
                        BotFormatter.log("Window still exists, trying force close", "WARNING")
                        
                except Exception as e:
                    BotFormatter.log(f"Failed to close specific window: {e}", "WARNING")
            
            # Method 2: Close by process name (more aggressive)
            return await self._close_game_by_process_name()
            
        except Exception as e:
            BotFormatter.log(f"Error closing bot window: {e}", "ERROR")
            return False
    
    async def _close_game_by_process_name(self):
        """Close Transformice processes by name"""
        try:
            closed_processes = []
            
            # Common Transformice process names
            process_patterns = [
                "transformice",
                "flashplayer",
                "adobe",
                "tfm"
            ]
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower() if proc_info['name'] else ''
                    cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''
                    exe_path = proc_info['exe'].lower() if proc_info['exe'] else ''
                    
                    # Check if it's a Transformice-related process
                    is_tfm_process = (
                        any(pattern in proc_name for pattern in process_patterns) or
                        'transformice' in cmdline or
                        'transformice' in exe_path or
                        ('flash' in proc_name and 'transformice' in cmdline)
                    )
                    
                    if is_tfm_process:
                        BotFormatter.log(f"Terminating process: {proc_info['name']} (PID: {proc_info['pid']})", "INFO")
                        
                        # Try graceful termination first
                        proc.terminate()
                        closed_processes.append(proc_info['name'])
                        
                        # Wait a bit, then force kill if still running
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            BotFormatter.log(f"Force killing process: {proc_info['name']}", "WARNING")
                            proc.kill()
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    BotFormatter.log(f"Error checking process: {e}", "DEBUG")
                    continue
            
            if closed_processes:
                BotFormatter.log(f"Closed processes: {', '.join(closed_processes)}", "SUCCESS")
                await asyncio.sleep(2)  # Wait for processes to fully close
            else:
                BotFormatter.log("No Transformice processes found to close", "INFO")
            
            return True
            
        except Exception as e:
            BotFormatter.log(f"Error closing game processes: {e}", "ERROR")
            return False
    
    async def _open_new_game_window(self):
        """Open a new game window"""
        try:
            # Method 1: Try configured Transformice path
            tfm_path = self.config.get('transformice_path')
            if tfm_path and os.path.exists(tfm_path):
                BotFormatter.log(f"Opening Transformice from configured path: {tfm_path}", "INFO")
                subprocess.Popen([tfm_path], cwd=os.path.dirname(tfm_path))
                return True
            
            # Method 2: Try common Transformice installation paths
            username = os.getenv('USERNAME', 'User')
            common_paths = [
                rf"C:\Users\{username}\AppData\Local\Transformice\Transformice.exe",
                rf"C:\Users\{username}\AppData\Roaming\Transformice\Transformice.exe",
                r"C:\Program Files\Transformice\Transformice.exe",
                r"C:\Program Files (x86)\Transformice\Transformice.exe",
                rf"C:\Users\{username}\Desktop\Transformice.exe",
                rf"C:\Users\{username}\Downloads\Transformice.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    BotFormatter.log(f"Found Transformice at: {path}", "SUCCESS")
                    subprocess.Popen([path], cwd=os.path.dirname(path))
                    return True
            
            # Method 3: Try Flash Player with Transformice SWF (if available)
            # This would require having the .swf file path
            
            # Method 4: Open browser to Transformice (fallback)
            BotFormatter.log("No local executable found, trying browser method", "INFO")
            chrome_profile = self.config.get('chrome_profile_path', '')
            
            try:
                if chrome_profile:
                    subprocess.Popen([
                        "chrome.exe",
                        "--new-window",
                        "https://www.transformice.com/",
                        f"--user-data-dir={chrome_profile}"
                    ])
                else:
                    subprocess.Popen([
                        "chrome.exe",
                        "--new-window", 
                        "https://www.transformice.com/"
                    ])
                
                BotFormatter.log("Opened Transformice in browser", "INFO")
                return True
                
            except Exception as e:
                BotFormatter.log(f"Browser method failed: {e}", "WARNING")
            
            # Method 5: Try default browser
            try:
                import webbrowser
                webbrowser.open("https://www.transformice.com/")
                BotFormatter.log("Opened Transformice in default browser", "INFO")
                return True
            except Exception as e:
                BotFormatter.log(f"Default browser method failed: {e}", "WARNING")
            
            BotFormatter.log("All methods to open game failed", "ERROR")
            return False
            
        except Exception as e:
            BotFormatter.log(f"Error opening new game window: {e}", "ERROR")
            return False
    
    async def _enter_login_credentials(self):
        """Enter login credentials automatically"""
        try:
            # Get credentials from config
            bot_username = self.config.get('bot_username', '')
            bot_password = self.config.get('bot_password', '')
            
            if not bot_username or not bot_password:
                BotFormatter.log("Bot credentials not configured in config file", "WARNING")
                BotFormatter.log("Add 'bot_username' and 'bot_password' to your config", "INFO")
                return False
            
            # Wait for login screen to appear
            await asyncio.sleep(2)
            
            # Find the new game window
            if self.window_controller:
                def find_new_window():
                    return self.window_controller.set_bot_window()
                
                success = await asyncio.get_event_loop().run_in_executor(None, find_new_window)
                if not success:
                    BotFormatter.log("Could not find new game window for login", "WARNING")
                    return False
            else:
                BotFormatter.log("No window controller available for login", "ERROR")
                return False
            
            BotFormatter.log(f"Entering credentials for: {bot_username}", "INFO")
            
            # Enter credentials
            def enter_credentials():
                try:
                    hwnd = self.window_controller.bot_window_handle
                    if not hwnd:
                        return False
                    
                    # Focus the window
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)
                    
                    # Clear any existing text (Ctrl+A)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, self.VK_CTRL, 0)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, self.VK_A, 0)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, self.VK_A, 0)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, self.VK_CTRL, 0)
                    time.sleep(0.1)
                    
                    # Type username
                    for char in bot_username:
                        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
                        time.sleep(0.02)
                    
                    # Tab to password field
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, self.VK_TAB, 0)
                    time.sleep(0.1)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, self.VK_TAB, 0)
                    time.sleep(0.3)
                    
                    # Type password
                    for char in bot_password:
                        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
                        time.sleep(0.02)
                    
                    # Press Enter to login
                    time.sleep(0.5)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, self.VK_RETURN, 0)
                    time.sleep(0.1)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, self.VK_RETURN, 0)
                    
                    BotFormatter.log("Login credentials entered successfully", "SUCCESS")
                    return True
                    
                except Exception as e:
                    BotFormatter.log(f"Error entering credentials: {e}", "ERROR")
                    return False
            
            success = await asyncio.get_event_loop().run_in_executor(None, enter_credentials)
            return success
            
        except Exception as e:
            BotFormatter.log(f"Error in login process: {e}", "ERROR")
            return False
    
    async def _update_window_controller(self):
        """Update window controller to find the new game window"""
        try:
            if self.window_controller:
                def update_controller():
                    return self.window_controller.set_bot_window()
                
                success = await asyncio.get_event_loop().run_in_executor(None, update_controller)
                if success:
                    BotFormatter.log("Window controller updated for new game window", "SUCCESS")
                else:
                    BotFormatter.log("Failed to update window controller", "WARNING")
                return success
            return False
        except Exception as e:
            BotFormatter.log(f"Error updating window controller: {e}", "ERROR")
            return False
    
    def get_required_config_keys(self):
        """Get list of required configuration keys"""
        return [
            'bot_username',      # Required: Bot account username
            'bot_password',      # Required: Bot account password
            'transformice_path', # Optional: Path to Transformice.exe
            'chrome_profile_path' # Optional: Chrome profile path for browser method
        ]
    
    def validate_config(self):
        """Validate that required configuration is present"""
        missing_keys = []
        
        if not self.config.get('bot_username'):
            missing_keys.append('bot_username')
        if not self.config.get('bot_password'):
            missing_keys.append('bot_password')
        
        if missing_keys:
            BotFormatter.log(f"Missing required config keys: {', '.join(missing_keys)}", "ERROR")
            return False
        
        return True


# Standalone testing function
async def test_reset_player():
    """Test the reset player functionality"""
    print("🧪 Testing Reset Player Module")
    print("=" * 50)
    
    # Mock config for testing
    test_config = {
        'bot_username': 'TestBot#1234',
        'bot_password': 'test_password',
        'transformice_path': None,
        'chrome_profile_path': ''
    }
    
    resetter = ResetWindowPlayer(test_config)
    
    # Validate config
    if not resetter.validate_config():
        print("❌ Configuration validation failed")
        return
    
    print("✅ Configuration validated")
    print(f"Bot username: {test_config['bot_username']}")
    print()
    
    # Mock send message callback
    async def mock_send_message(message):
        print(f"[CHAT] {message}")
    
    # Run the reset process
    print("🚀 Starting reset process...")
    success = await resetter.reset_player(mock_send_message)
    
    if success:
        print("\n✅ Reset player test completed successfully!")
    else:
        print("\n❌ Reset player test failed!")


if __name__ == "__main__":
    # Run standalone test
    asyncio.run(test_reset_player())