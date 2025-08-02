#!/usr/bin/env python3
"""
Simple runner script for the Transformice AI Bot
This is an alternative to main.py with some preset configurations
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.formatter import BotFormatter
from managers.bot_manager import BotManager

def main():
    """Simple main function with basic setup"""
    
    # Check for Windows API
    try:
        import win32gui
        BotFormatter.log("✅ Windows API available", "SUCCESS")
    except ImportError:
        BotFormatter.log("❌ Windows API not available. Install with: pip install pywin32", "ERROR")
        sys.exit(1)
    
    # Check for Selenium
    try:
        from selenium import webdriver
        BotFormatter.log("✅ Selenium available", "SUCCESS")
    except ImportError:
        BotFormatter.log("❌ Selenium not available. Install with: pip install selenium", "ERROR")
        sys.exit(1)
    
    # Basic configuration
    config_overrides = {
        'host_main_port': 11801,
        'host_satellite_port': 12801,
        'headless_browser': False,  # Set to True to hide browser
        'controller_username': None,  # Set your main account username here
    }
    
    # Create and run bot
    manager = BotManager()
    manager.apply_overrides(config_overrides)
    
    BotFormatter.log("Starting Transformice AI Bot...", "BOT")
    BotFormatter.log("Configure your controller username in this file for better experience", "INFO")
    
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        BotFormatter.log("Bot stopped by user", "INFO")
    except Exception as e:
        BotFormatter.log(f"Error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()