# Transformice AI Bot with Browser-Based Gemini

A sophisticated Transformice bot that integrates with Google Gemini AI through browser automation for intelligent chat responses and game control.

## Features

- **AI Chat Integration**: Uses browser automation to interact with Google Gemini for intelligent responses
- **Game Control**: Complete movement control including walking, jumping, combos, and spam actions
- **Window Control**: Background window manipulation without requiring focus
- **Dual Communication**: Supports both room chat and whisper commands
- **Human-like Behavior**: Realistic typing patterns and response delays

## Project Structure

```
tfm_ai_bot/
├── main.py                    # Entry point
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuration management
├── core/
│   ├── __init__.py
│   ├── formatter.py          # Terminal output formatting
│   ├── window_controller.py  # Windows API game control
│   ├── game_controller.py    # Main bot logic
│   └── command_handlers.py   # Command execution
├── ai/
│   ├── __init__.py
│   └── browser_gemini.py     # Browser-based Gemini AI
└── managers/
    ├── __init__.py
    └── bot_manager.py        # Bot lifecycle management
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install ChromeDriver:**
   - Download ChromeDriver from https://chromedriver.chromium.org/
   - Add it to your system PATH

3. **Windows API Setup:**
   ```bash
   pip install pywin32
   ```

## Usage

### Basic Usage
```bash
python main.py
```

### With Configuration
```bash
python main.py --config bot_config.json --controller YourUsername
```

### Command Line Options
- `--config`: Path to configuration file
- `--main-port`: Main server port (default: 11801)
- `--satellite-port`: Satellite server port (default: 12801)
- `--controller`: Username of the controller account
- `--headless`: Run browser in headless mode

## Setup Instructions

1. Start the bot first
2. Connect your BOT account to localhost:11801
3. Connect your MAIN account to localhost:11801
4. Both accounts should be in the same room
5. The bot will automatically open a browser for AI functionality

## Available Commands

### Movement Commands
- `$move right 50` - Move bot right 50 pixels
- `$jump` - Make bot jump
- `$walk right` - Start continuous walking
- `$stop` - Stop all movement
- `$spam jump 5` - Jump 5 times rapidly
- `$combo right jump` - Move right then jump

### AI Commands
- `$ai What is 2+2?` - Ask Gemini AI a question
- `$ask How are you?` - Alternative AI command
- `$aiopen` - Open/restart browser
- `$aiclose` - Close browser

### Bot Control Commands
- `$status` - Show bot status
- `$chat Hello world!` - Make bot say something
- `$on` - Enable bot
- `$off` - Disable bot
- `$reset` - Reset all states
- `$find` - Find game window

### Window Management Commands
- `$windows` - List all Transformice windows
- `$window 1` - Switch to window 1 (bot account)
- `$window 2` - Switch to window 2 (main account)  
- `$select 1` - Same as $window 1 (by number)
- `$select 3` - Same as $window 3 (by number)
- `$select bot` - Select window containing "bot" in title
- `$select main` - Select window containing "main" in title
- `$current` - Show current window information
- `$debug` - Debug window detection

## Configuration

Create a `config.json` file:

```json
{
  "host_address": null,
  "host_main_port": 11801,
  "host_satellite_port": 12801,
  "expected_address": "localhost",
  "controller_username": "YourMainAccount",
  "browser_type": "chrome",
  "headless_browser": false
}
```

## Window Management

The bot supports managing multiple Transformice windows, which is perfect when you have separate windows for your bot account and main account.

### Window Commands

1. **List Windows**: `$windows`
   - Shows all available Transformice windows
   - Displays window numbers and titles
   - Indicates which window is currently selected

2. **Switch by Number**: `$window [number]`
   - `$window 1` - Switch to first window
   - `$window 2` - Switch to second window
   - Numbers correspond to the list from `$windows`

3. **Select by Number or Title**: `$select [number or text]`
   - `$select 1` - Select window 1 (same as $window 1)
   - `$select 2` - Select window 2 (same as $window 2)  
   - `$select 3` - Select window 3 (same as $window 3)
   - `$select bot` - Select window containing "bot"
   - `$select main` - Select window containing "main"
   - `$select Adobe` - Select window containing "Adobe"

4. **Current Window**: `$current`
   - Shows information about currently selected window

### Typical Usage

If you have two windows open:
1. Window 1: "Adobe Flash Player - Bot Account"
2. Window 2: "Adobe Flash Player - Main Account"

You can:
- Use `$window 1` to control the bot account
- Use `$window 2` to control the main account
- Use `$select bot` to automatically find the bot window
- Use `$windows` to see which window is currently active

### AI Integration
- Uses Selenium to automate Google Gemini chat
- Supports multiple response parsing methods
- Human-like response timing and message splitting
- Automatic error handling and fallbacks

### Game Control
- Background window control without focus stealing
- Human-like typing patterns for chat
- Precise movement timing and control
- Support for complex command combinations

### Communication
- Works with both room chat and whispers
- Automatic account detection and pairing
- Command source tracking and validation
- Debug packet inspection for whisper detection

## Requirements

- Windows OS (for Windows API game control)
- Python 3.7+
- Google Chrome browser
- ChromeDriver
- Active Transformice accounts

## Troubleshooting

### Common Issues

1. **"Windows API not available"**
   - Install pywin32: `pip install pywin32`

2. **"Browser failed to start"**
   - Ensure Chrome is installed
   - Download and install ChromeDriver
   - Add ChromeDriver to system PATH

3. **"No Transformice windows found"**
   - Make sure Transformice is running
   - Use `$find` command to re-detect windows

4. **Commands not working**
   - Check that controller username is set correctly
   - Ensure both accounts are in the same room
   - Verify whisper/chat permissions

## Development

### Adding New Commands

1. Add regex pattern in `core/game_controller.py`
2. Add command handler in `core/command_handlers.py`
3. Update help text in initialization

### Extending AI Features

1. Modify `ai/browser_gemini.py` for new AI providers
2. Add configuration options in `config/settings.py`
3. Update command processing logic

## License

This project is for educational purposes. Please respect Transformice's terms of service.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Disclaimer

This bot is for educational and research purposes. Users are responsible for complying with Transformice's terms of service and any applicable rules or regulations.
