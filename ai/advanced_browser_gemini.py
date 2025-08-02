#!/usr/bin/env python3
"""
Fixed Advanced Browser-based Gemini AI integration
REPLACE: ai/advanced_browser_gemini.py
"""

import asyncio
import time
from core.formatter import BotFormatter

# Browser automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class AIPersonality:
    """Represents an AI personality configuration"""
    
    def __init__(self, name, language, topic, custom_instructions=""):
        self.name = name
        self.language = language
        self.topic = topic
        self.custom_instructions = custom_instructions
        self.tab_handle = None
        self.is_initialized = False
        self.prompt_sent = False
    
    def generate_system_prompt(self):
        """Generate the system prompt for this personality"""
        
        # Language configurations
        language_configs = {
            'darija': {
                'instruction': "You MUST respond in Moroccan Darija using Latin script (like: 'Salam, kifach nta?', 'Labas 3lik', 'Ash kat dir?')",
                'examples': "Examples: 'Ahlan! Kifach nta?', 'Labas 3lik khouya', 'Wach kat9ayed m3ana?'"
            },
            'arabic': {
                'instruction': "You MUST respond in Arabic using Arabic script",
                'examples': "أمثلة: 'أهلاً! كيفك؟', 'أهلاً وسهلاً'"
            },
            'french': {
                'instruction': "You MUST respond in French",
                'examples': "Exemples: 'Salut! Comment ça va?', 'Bonjour mon ami!'"
            },
            'english': {
                'instruction': "Respond in English",
                'examples': "Examples: 'Hey! How are you?', 'What's up buddy?'"
            }
        }
        
        # Topic configurations
        topic_configs = {
            'anime': {
                'personality': "You are an enthusiastic anime fan who loves discussing anime, manga, characters, and storylines",
                'interests': "anime series, manga, Japanese culture, character development, plot analysis, recommendations"
            },
            'gaming': {
                'personality': "You are a passionate gamer who loves discussing games, strategies, and gaming culture",
                'interests': "video games, gaming strategies, game reviews, gaming news, esports"
            },
            'casual': {
                'personality': "You are a friendly, casual chat companion who enjoys everyday conversations",
                'interests': "daily life, hobbies, general topics, friendly chat"
            },
            'tech': {
                'personality': "You are a tech-savvy assistant who loves discussing technology, programming, and innovation",
                'interests': "technology, programming, software, hardware, tech news"
            },
            'sports': {
                'personality': "You are a sports enthusiast who loves discussing various sports, teams, and athletes",
                'interests': "sports, teams, athletes, matches, sports news"
            }
        }
        
        # Get configurations
        lang_config = language_configs.get(self.language, language_configs['english'])
        topic_config = topic_configs.get(self.topic, topic_configs['casual'])
        
        # Build the system prompt as a single line
        system_prompt = f"IMPORTANT SYSTEM INSTRUCTIONS: {lang_config['instruction']} {lang_config['examples']} PERSONALITY: {topic_config['personality']} YOUR INTERESTS: {topic_config['interests']} CHAT RULES: Keep responses under 200 characters for game chat, be enthusiastic about {self.topic} topics, use emojis sparingly but appropriately, be natural and conversational, remember this is a game chat environment, stay in character as {self.name}. {self.custom_instructions} IMPORTANT: From now on, ALL your responses should follow these instructions automatically. You don't need to be reminded again."
        
        return system_prompt


class AdvancedBrowserGemini:
    """Advanced Browser-based Gemini AI with multiple personalities"""
    
    def __init__(self, browser_type="chrome", headless=False):
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None
        self.gemini_url = "https://gemini.google.com/"
        self.is_initialized = False
        
        # AI Personalities management
        self.personalities = {}  # name -> AIPersonality
        self.current_personality = None
        
        # Your specific Chrome profile path
        self.chrome_profile_path = r"C:\Users\moaad\AppData\Local\Google\Chrome\User Data\Profile 2"
        
        # Default personalities
        self._setup_default_personalities()
    
    def _setup_default_personalities(self):
        """Setup some default AI personalities"""
        defaults = [
            ("default", "english", "casual", ""),
        ]
        
        for name, lang, topic, custom in defaults:
            self.personalities[name] = AIPersonality(name, lang, topic, custom)
    
    async def initialize(self):
        """Initialize the browser if not already initialized"""
        if self.is_initialized:
            BotFormatter.log("Browser already initialized", "BROWSER")
            return True
            
        if not SELENIUM_AVAILABLE:
            BotFormatter.log("Selenium not available. Install with: pip install selenium", "ERROR")
            return False
        
        try:
            BotFormatter.log("Initializing browser for Gemini...", "BROWSER")
            
            # Setup Chrome options with your specific profile
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1200,800")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use your specific Chrome profile
            chrome_options.add_argument(f"--user-data-dir={self.chrome_profile_path}")
            
            # Initialize the driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to Gemini
            BotFormatter.log("Opening Gemini in browser...", "BROWSER")
            self.driver.get(self.gemini_url)
            await asyncio.sleep(5)
            
            self.is_initialized = True
            BotFormatter.log("Browser initialized successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            BotFormatter.log(f"Failed to initialize browser: {e}", "ERROR")
            return False
    
    async def create_new_ai(self, ai_args):
        """Create a new AI personality from command arguments"""
        # Parse arguments like --darija --anime --name "MyAI"
        language = "english"
        topic = "casual"
        name = None
        custom_instructions = ""
        
        # Parse the arguments
        args = ai_args.strip().split()
        i = 0
        while i < len(args):
            arg = args[i].lower()
            
            if arg.startswith('--'):
                flag = arg[2:]  # Remove --
                
                # Language flags
                if flag in ['darija', 'arabic', 'french', 'english']:
                    language = flag
                
                # Topic flags
                elif flag in ['anime', 'gaming', 'casual', 'tech', 'sports']:
                    topic = flag
                
                # Name flag (expects a value)
                elif flag == 'name' and i + 1 < len(args):
                    i += 1
                    name = args[i].strip('"\'')
                
                # Custom instruction flag (expects a value)
                elif flag == 'custom' and i + 1 < len(args):
                    i += 1
                    custom_instructions = args[i].strip('"\'')
            
            i += 1
        
        # Generate name if not provided
        if not name:
            name = f"{language}_{topic}_{int(time.time() % 10000)}"
        
        # Create the personality
        personality = AIPersonality(name, language, topic, custom_instructions)
        self.personalities[name] = personality
        
        BotFormatter.log(f"Created AI personality: {name} (Language: {language}, Topic: {topic})", "AI")
        
        # Initialize the personality
        success = await self._initialize_personality(personality)
        if success:
            self.current_personality = personality
            return "Done new personality"  # Exactly what you wanted
        else:
            return f"❌ Failed to initialize AI: {name}"
    
    async def _initialize_personality(self, personality):
        """Initialize a personality in a new tab"""
        try:
            # Make sure browser is open
            if not self.is_initialized:
                if not await self.initialize():
                    return False
            
            # Open new tab for this personality
            BotFormatter.log(f"Creating new tab for {personality.name}", "BROWSER")
            self.driver.execute_script("window.open('');")
            await asyncio.sleep(1)
            
            # Switch to the new tab
            tabs = self.driver.window_handles
            new_tab = tabs[-1]
            self.driver.switch_to.window(new_tab)
            personality.tab_handle = new_tab
            
            # Navigate to Gemini in the new tab
            self.driver.get(self.gemini_url)
            await asyncio.sleep(3)
            
            # Send the system prompt to configure this AI
            system_prompt = personality.generate_system_prompt()
            BotFormatter.log(f"Sending system prompt to {personality.name}", "BROWSER")
            response = await self._send_message(system_prompt)
            
            if response:
                personality.is_initialized = True
                personality.prompt_sent = True
                BotFormatter.log(f"Personality {personality.name} initialized successfully", "AI")
                return True
            else:
                BotFormatter.log(f"Failed to send system prompt to {personality.name}", "ERROR")
                return False
                
        except Exception as e:
            BotFormatter.log(f"Error initializing personality {personality.name}: {e}", "ERROR")
            return False
    
    async def switch_to_ai(self, ai_name):
        """Switch to a specific AI personality"""
        if ai_name not in self.personalities:
            return f"❌ AI '{ai_name}' not found. Available: {', '.join(self.personalities.keys())}"
        
        personality = self.personalities[ai_name]
        
        # Initialize if not already done
        if not personality.is_initialized:
            success = await self._initialize_personality(personality)
            if not success:
                return f"❌ Failed to initialize AI: {ai_name}"
        
        # Switch to the personality's tab
        try:
            self.driver.switch_to.window(personality.tab_handle)
            self.current_personality = personality
            BotFormatter.log(f"Switched to AI: {ai_name}", "AI")
            return f"✅ Switched to AI: {ai_name} ({personality.language}, {personality.topic})"
        except Exception as e:
            BotFormatter.log(f"Error switching to AI {ai_name}: {e}", "ERROR")
            return f"❌ Error switching to AI: {ai_name}"
    
    async def ask_question(self, question):
        """Ask a question to the current AI personality - ONLY sends the user's question"""
        if not self.current_personality:
            # Use default personality
            if 'default' not in self.personalities:
                return "❌ No AI personality active. Use $newai to create one."
            
            await self.switch_to_ai('default')
        
        if not self.current_personality.is_initialized:
            return "❌ Current AI not initialized"
        
        try:
            # Switch to the current personality's tab
            self.driver.switch_to.window(self.current_personality.tab_handle)
            
            # Send ONLY the user's question (no additional prompts)
            BotFormatter.log(f"Sending user question: {question}", "BROWSER")
            response = await self._send_message(question)  # Just the question!
            
            if response:
                return response
            else:
                return "❌ Could not get response from AI"
                
        except Exception as e:
            BotFormatter.log(f"Error asking question: {e}", "ERROR")
            return f"❌ Error: {str(e)[:50]}..."
    
    async def _send_message(self, message):
        """Send a message to Gemini in the current tab"""
        try:
            # Find input element
            input_element = await self._find_input_element()
            if not input_element:
                return None
            
            # Input the message
            await self._input_message(input_element, message)
            
            # Submit
            await self._submit_message(input_element)
            
            # Wait for and extract response
            response = await self._wait_for_response()
            return response
            
        except Exception as e:
            BotFormatter.log(f"Error sending message: {e}", "ERROR")
            return None
    
    async def _find_input_element(self):
        """Find the input element"""
        selectors = [
            "textarea[placeholder*='Enter a prompt']",
            "textarea[placeholder*='Ask Gemini']",
            "textarea",
            "[contenteditable='true']",
            "[role='textbox']"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return element
            except TimeoutException:
                continue
        
        return None
    
    async def _input_message(self, input_element, message):
        """Input message into the element"""
        try:
            input_element.clear()
            await asyncio.sleep(0.2)
            input_element.click()
            await asyncio.sleep(0.2)
            
            # Try send_keys first
            input_element.send_keys(message)
            await asyncio.sleep(0.3)
            
        except Exception as e:
            # Fallback to JavaScript
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                input_element, message
            )
            await asyncio.sleep(0.3)
    
    async def _submit_message(self, input_element):
        """Submit the message"""
        try:
            input_element.send_keys(Keys.RETURN)
        except:
            # Try finding submit button
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Send']")
                submit_btn.click()
            except:
                # Fallback
                input_element.send_keys(Keys.CONTROL + Keys.RETURN)
    
    async def _wait_for_response(self):
        """Wait for and extract response"""
        await asyncio.sleep(3)  # Wait for response to start
        
        # Try to find response elements
        selectors = [
            "article:last-child",
            "[data-test-id*='conversation-turn']:last-child",
            ".model-response-text:last-child"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    text = elements[-1].text.strip()
                    if text and len(text) > 5:
                        return text
            except:
                continue
        
        return None
    
    def list_personalities(self):
        """List all available AI personalities"""
        if not self.personalities:
            return "No AI personalities created yet."
        
        result = "Available AI Personalities:\n"
        for name, personality in self.personalities.items():
            status = "✅ Active" if personality.is_initialized else "⚪ Not initialized"
            current = "👈 CURRENT" if personality == self.current_personality else ""
            result += f"• {name}: {personality.language.title()} + {personality.topic.title()} {status} {current}\n"
        
        return result.strip()
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                BotFormatter.log("Advanced browser closed", "BROWSER")
            except:
                pass
            self.driver = None
            self.is_initialized = False