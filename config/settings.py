#!/usr/bin/env python3
"""
Configuration management for the Transformice AI Bot
"""

import json
from pathlib import Path


class BotConfig:
    """Configuration manager for the bot"""
    
    DEFAULT_CONFIG = {
        'host_address': None,
        'host_main_port': 11801,
        'host_satellite_port': 12801,
        'expected_address': 'localhost',
        'main_server_address': None,
        'main_server_ports': None,
        'controller_username': None,  # Set this to your main account name
        'browser_type': 'chrome',     # Browser to use for Gemini
        'headless_browser': False,    # Set to True to hide browser window
    }
    
    def __init__(self, config_file=None):
        self.config = self._load_config(config_file)
    
    def _load_config(self, config_file):
        """Load configuration from file"""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded_config)
                return config
        
        return self.DEFAULT_CONFIG.copy()
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update(updates)
    
    def save(self, config_file):
        """Save configuration to file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_bot_config(self):
        """Extract bot configuration"""
        return {
            'host_address': self.get('host_address'),
            'host_main_port': self.get('host_main_port', 11801),
            'host_satellite_port': self.get('host_satellite_port', 12801),
            'expected_address': self.get('expected_address', 'localhost'),
            'main_server_address': self.get('main_server_address'),
            'main_server_ports': self.get('main_server_ports'),
        }
    
    def create_ai_config(self):
        """Extract AI configuration"""
        return {
            'browser_type': self.get('browser_type', 'chrome'),
            'headless': self.get('headless_browser', False),
        }
    
    def __getitem__(self, key):
        """Allow dict-like access"""
        return self.config[key]
    
    def __setitem__(self, key, value):
        """Allow dict-like assignment"""
        self.config[key] = value
    
    def __contains__(self, key):
        """Allow 'in' operator"""
        return key in self.config