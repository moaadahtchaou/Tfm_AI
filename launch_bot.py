#!/usr/bin/env python3
"""
Bot Launcher - Ensures proper import paths and launches the bot
"""

import sys
import os
import argparse
import asyncio

# Ensure the current directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import our modules
try:
    from core.formatter import BotFormatter
    from managers.bot_manager import BotManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all files are in the correct directories as shown in the README")
    sys.exit(1)

def main():
    """Main entry point with proper error handling"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Transformice AI Bot with Browser-Based Gemini")
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--main-port', type=int, default=11801,
                       help='Main server port (default: 11801)')
    parser.add_argument('--satellite-port', type=int, default=12801,
                       help='Satellite server port (default: 12801)')
    parser.add_argument('--controller', help='Username of the controller account')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode (hidden)')
    
    args = parser.parse_args()
    
    # Check dependencies
    BotFormatter.log("Checking dependencies...", "INFO")
    
    # Check Windows API
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
        BotFormatter.log("✅ Windows API available", "SUCCESS")
    except ImportError:
        BotFormatter.log("❌ Windows API not available!", "ERROR")
        BotFormatter.log("Please install: pip install pywin32", "ERROR")
        sys.exit(1)
    
    # Check Caseus
    try:
        import caseus
        BotFormatter.log("✅ Caseus library available", "SUCCESS")
    except ImportError:
        BotFormatter.log("❌ Caseus library not available!", "ERROR")
        BotFormatter.log("Please install caseus library", "ERROR")
        sys.exit(1)
    
    # Check Selenium (optional for AI features)
    try:
        from selenium import webdriver
        BotFormatter.log("✅ Selenium available - AI features enabled", "SUCCESS")
    except ImportError:
        BotFormatter.log("⚠️  Selenium not available - AI features disabled", "WARNING")
        BotFormatter.log("Install with: pip install selenium", "WARNING")
    
    # Configuration overrides
    config_overrides = {}
    if args.main_port != 11801:
        config_overrides['host_main_port'] = args.main_port
    if args.satellite_port != 12801:
        config_overrides['host_satellite_port'] = args.satellite_port
    if args.controller:
        config_overrides['controller_username'] = args.controller
    if args.headless:
        config_overrides['headless_browser'] = True
    
    # Create and configure bot manager
    try:
        manager = BotManager(args.config)
        manager.apply_overrides(config_overrides)
        
        BotFormatter.log("Starting bot...", "BOT")
        asyncio.run(manager.run())
        
    except KeyboardInterrupt:
        BotFormatter.log("Bot stopped by user", "INFO")
    except Exception as e:
        BotFormatter.log(f"Error running bot: {e}", "ERROR")
        import traceback
        BotFormatter.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
        sys.exit(1)

if __name__ == "__main__":
    main()