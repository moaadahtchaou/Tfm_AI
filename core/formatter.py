#!/usr/bin/env python3
"""
Terminal output formatter for the bot
"""

from datetime import datetime

# Try to import colorama for colored output
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = MockColor()
    COLORS_AVAILABLE = False


class BotFormatter:
    """Terminal output formatter for the bot"""
    
    @staticmethod
    def log(message, category="BOT"):
        """Print a formatted log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if COLORS_AVAILABLE:
            colors = {
                "BOT": Fore.GREEN + Style.BRIGHT,
                "COMMAND": Fore.YELLOW + Style.BRIGHT,
                "INPUT": Fore.CYAN + Style.BRIGHT,
                "ERROR": Fore.RED + Style.BRIGHT,
                "INFO": Fore.BLUE,
                "SUCCESS": Fore.GREEN,
                "WARNING": Fore.YELLOW,
                "REMOTE": Fore.WHITE + Back.CYAN,
                "WINDOW": Fore.MAGENTA,
                "DEBUG": Fore.WHITE + Style.DIM,
                "AI": Fore.CYAN + Style.BRIGHT,
                "BROWSER": Fore.BLUE + Style.BRIGHT,
            }
            color = colors.get(category, Fore.WHITE)
            print(f"{Fore.WHITE}[{timestamp}] {color}[{category}]{Style.RESET_ALL} {message}")
        else:
            print(f"[{timestamp}] [{category}] {message}")