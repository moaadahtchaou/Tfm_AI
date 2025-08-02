#!/usr/bin/env python3
"""
Bot Manager for the background game controller
"""

import signal
from core.formatter import BotFormatter
from core.game_controller import BackgroundGameController
from core.command_handlers import CommandHandlers
from config.settings import BotConfig


# Combine the game controller with command handlers
class EnhancedGameController(BackgroundGameController, CommandHandlers):
    """Game controller with command handling capabilities"""
    pass


class BotManager:
    """Manager for the background game controller"""
    
    def __init__(self, config_file=None):
        self.config = BotConfig(config_file)
        self.bot = None
        self.running = False
    
    def create_bot(self):
        """Create the bot instance"""
        bot_config = self.config.create_bot_config()
        
        # Remove None values
        bot_config = {k: v for k, v in bot_config.items() if v is not None}
        
        # Add AI configuration
        full_config = dict(self.config.config)
        full_config['ai_config'] = self.config.create_ai_config()
        
        self.bot = EnhancedGameController(
            config=full_config,
            **bot_config
        )
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            BotFormatter.log(f"Received signal {signum}, shutting down...", "WARNING")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def apply_overrides(self, overrides):
        """Apply configuration overrides"""
        self.config.update(overrides)
    
    async def run(self):
        """Main run method"""
        self.setup_signal_handlers()
        self.create_bot()
        self.running = True
        
        self._log_startup_info()
        
        try:
            await self.bot.start()
        except KeyboardInterrupt:
            BotFormatter.log("Shutdown requested by user", "WARNING")
        except Exception as e:
            BotFormatter.log(f"Bot error: {e}", "ERROR")
        finally:
            self.running = False
            if self.bot:
                await self.bot.shutdown()
            BotFormatter.log("AI Bot stopped", "BOT")
    
    def _log_startup_info(self):
        """Log startup information"""
        BotFormatter.log("=" * 60, "BOT")
        BotFormatter.log("TRANSFORMICE AI BOT WITH BROWSER GEMINI", "BOT")
        BotFormatter.log("=" * 60, "BOT")
        BotFormatter.log(f"Listening on ports {self.config.get('host_main_port', 11801)}/{self.config.get('host_satellite_port', 12801)}", "INFO")
        BotFormatter.log("", "INFO")
        BotFormatter.log("SETUP INSTRUCTIONS:", "INFO")
        BotFormatter.log("1. Start this bot first", "INFO")
        BotFormatter.log("2. Connect your BOT account to localhost:11801", "INFO")
        BotFormatter.log("3. Connect your MAIN account to localhost:11801", "INFO")
        BotFormatter.log("4. Both accounts should be in the same room", "INFO")
        BotFormatter.log("5. Bot will open browser automatically for AI!", "SUCCESS")
        BotFormatter.log("", "INFO")
        BotFormatter.log("AVAILABLE COMMANDS:", "INFO")
        BotFormatter.log("Movement: $move, $jump, $walk, $stop, $spam, $combo", "INFO")
        BotFormatter.log("Browser AI: $ai [question], $ask [question]", "AI")
        BotFormatter.log("AI Control: $aiopen, $aiclose", "AI")
        BotFormatter.log("Bot Control: $status, $chat, $on, $off, $reset, $find", "INFO")
        BotFormatter.log("", "INFO")
        
        try:
            from selenium import webdriver
            BotFormatter.log("✅ Browser automation ready - Gemini AI available!", "AI")
        except ImportError:
            BotFormatter.log("⚠️  Install Selenium for AI features:", "WARNING")
            BotFormatter.log("   pip install selenium", "WARNING")
            BotFormatter.log("   Download ChromeDriver and add to PATH", "WARNING")
        
        BotFormatter.log("", "INFO")
        BotFormatter.log("Press Ctrl+C to stop", "INFO")
        BotFormatter.log("=" * 60, "BOT")