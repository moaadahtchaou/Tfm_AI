#!/usr/bin/env python3
"""
Main entry point for Transformice AI Bot with Browser-Based Gemini
"""

import asyncio
import argparse
import sys
import os

# Add the current directory to Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.formatter import BotFormatter
from managers.bot_manager import BotManager

# Windows API availability check
try:
    import win32gui
    import win32con
    import win32api
    import win32process
    import win32clipboard
    import ctypes
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False


def main():
    """Main entry point"""
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
    
    # Check Windows API availability
    if not WINDOWS_API_AVAILABLE:
        print("ERROR: Windows API not available!")
        print("Please install: pip install pywin32")
        sys.exit(1)
    
    # Override config with command line arguments
    config_overrides = {}
    if args.main_port != 11801:
        config_overrides['host_main_port'] = args.main_port
    if args.satellite_port != 12801:
        config_overrides['host_satellite_port'] = args.satellite_port
    if args.controller:
        config_overrides['controller_username'] = args.controller
    if args.headless:
        config_overrides['headless_browser'] = True
    
    # Create and run bot manager
    manager = BotManager(args.config)
    manager.apply_overrides(config_overrides)
    
    try:
        asyncio.run(manager.run())
    except Exception as e:
        BotFormatter.log(f"Error running bot: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()