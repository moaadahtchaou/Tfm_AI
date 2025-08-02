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
        
        # Make sure browser is initialized
        if not self.is_initialized:
            if not await self.initialize():
                return "❌ Failed to start browser"
        
        # Create the personality object but DON'T add it to personalities yet
        personality = AIPersonality(name, language, topic, custom_instructions)
        
        BotFormatter.log(f"Attempting to create AI personality: {name} (Language: {language}, Topic: {topic})", "AI")
        
        # Try to initialize the personality
        success = await self._initialize_personality(personality)
        if success:
            # Only add to personalities if initialization succeeded
            self.personalities[name] = personality
            self.current_personality = personality
            BotFormatter.log(f"Successfully created and initialized AI: {name}", "AI")
            return "Done new personality"
        else:
            # Don't save failed personalities
            BotFormatter.log(f"Failed to initialize AI personality: {name}", "ERROR")
            return "Failed to initialize AI. Check browser connection."
    
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
            await asyncio.sleep(2)  # Increased wait time
            
            # Switch to the new tab
            tabs = self.driver.window_handles
            new_tab = tabs[-1]
            self.driver.switch_to.window(new_tab)
            personality.tab_handle = new_tab
            
            # Navigate to Gemini in the new tab
            BotFormatter.log("Navigating to Gemini in new tab", "BROWSER")
            self.driver.get(self.gemini_url)
            await asyncio.sleep(5)  # Increased wait time for page load
            
            # Check if page loaded properly
            try:
                page_title = self.driver.title
                BotFormatter.log(f"Page loaded with title: {page_title}", "BROWSER")
                
                if "Gemini" not in page_title and "Google" not in page_title:
                    BotFormatter.log(f"Warning: Unexpected page title: {page_title}", "WARNING")
                    
            except Exception as e:
                BotFormatter.log(f"Could not get page title: {e}", "WARNING")
            
            # Try to detect if we need to sign in
            try:
                sign_in_elements = self.driver.find_elements(By.CSS_SELECTOR, "[href*='signin'], [href*='login'], button[data-action*='signin']")
                if sign_in_elements:
                    BotFormatter.log("Detected sign-in page - you may need to log into Google first", "WARNING")
                    return False
            except:
                pass
            
            # Send the system prompt to configure this AI
            system_prompt = personality.generate_system_prompt()
            BotFormatter.log(f"Sending system prompt to {personality.name}", "BROWSER")
            BotFormatter.log(f"System prompt length: {len(system_prompt)} characters", "DEBUG")
            
            response = await self._send_message(system_prompt)
            
            if response:
                personality.is_initialized = True
                personality.prompt_sent = True
                BotFormatter.log(f"Personality {personality.name} initialized successfully", "AI")
                BotFormatter.log(f"Initial response: {response[:100]}...", "DEBUG")
                return True
            else:
                BotFormatter.log(f"Failed to send system prompt to {personality.name}", "ERROR")
                return False
                
        except Exception as e:
            BotFormatter.log(f"Error initializing personality {personality.name}: {e}", "ERROR")
            import traceback
            BotFormatter.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
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
        # Check if we have any AI personality set up
        if not self.current_personality:
            # Check if we have any personalities at all (even failed ones)
            if not self.personalities:
                return "No AI personality created yet. Use $newai --darija --anime first!"
            else:
                # We have personalities but none are current (probably all failed)
                return "No working AI personality. Try $newai --darija --anime again!"
        
        if not self.current_personality.is_initialized:
            return "Current AI not initialized. Use $newai to create an AI first!"
        
        try:
            # Switch to the current personality's tab
            self.driver.switch_to.window(self.current_personality.tab_handle)
            
            # Send ONLY the user's question (no additional prompts)
            BotFormatter.log(f"Sending user question: {question}", "BROWSER")
            response = await self._send_message(question)  # Just the question!
            
            if response:
                return response
            else:
                return "Could not get response from AI"
                
        except Exception as e:
            BotFormatter.log(f"Error asking question: {e}", "ERROR")
            return f"Error: {str(e)[:50]}..."
    
    async def _send_message(self, message):
        """Send a message to Gemini in the current tab"""
        try:
            BotFormatter.log(f"Attempting to send message: {message[:50]}...", "DEBUG")
            
            # Find input element
            input_element = await self._find_input_element()
            if not input_element:
                BotFormatter.log("No input element found", "ERROR")
                return None
            
            BotFormatter.log("Input element found, preparing to send message", "DEBUG")
            
            # Input the message
            await self._input_message(input_element, message)
            
            # Submit
            await self._submit_message(input_element)
            
            # Wait for and extract response
            response = await self._wait_for_response()
            
            if response:
                BotFormatter.log(f"Got response: {response[:100]}...", "DEBUG")
                return response
            else:
                BotFormatter.log("No response received", "ERROR")
                return None
            
        except Exception as e:
            BotFormatter.log(f"Error sending message: {e}", "ERROR")
            import traceback
            BotFormatter.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
            return None
    
    async def _find_input_element(self):
        """Find the input element with better detection based on actual HTML structure"""
        # Based on your HTML, the structure is:
        # rich-textarea > div.ql-editor.textarea.new-input-ui.ql-blank[contenteditable="true"]
        
        selectors = [
            # The actual structure from your screenshot
            "rich-textarea div[contenteditable='true']",
            "div.ql-editor[contenteditable='true']", 
            "div.textarea[contenteditable='true']",
            "div.new-input-ui[contenteditable='true']",
            
            # More specific combinations
            "rich-textarea div.ql-editor.textarea",
            "div[data-placeholder='Ask Gemini']",
            "div[aria-label*='Enter a prompt']",
            
            # Fallback selectors
            "div[contenteditable='true'][role='textbox']",
            "[contenteditable='true']",
            "textarea[placeholder*='Ask Gemini']",
            "textarea"
        ]
        
        # Wait for page to be ready
        await asyncio.sleep(2)
        
        for i, selector in enumerate(selectors):
            try:
                BotFormatter.log(f"Trying input selector {i+1}/{len(selectors)}: {selector}", "DEBUG")
                
                # Try to find with explicit wait
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Verify the element is actually the input we want
                if element.is_displayed() and element.is_enabled():
                    BotFormatter.log(f"Found input element with selector: {selector}", "SUCCESS")
                    return element
                
            except TimeoutException:
                BotFormatter.log(f"Selector timeout: {selector}", "DEBUG")
                continue
            except Exception as e:
                BotFormatter.log(f"Error with selector {selector}: {e}", "DEBUG")
                continue
        
        # If all selectors fail, try to find any contenteditable element
        try:
            BotFormatter.log("Trying fallback: any contenteditable element", "DEBUG")
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
            
            for element in all_elements:
                if element.is_displayed() and element.is_enabled():
                    # Check if it looks like an input (not too large, not containing lots of text)
                    if element.size['height'] < 200:  # Reasonable input height
                        BotFormatter.log(f"Found fallback contenteditable element", "SUCCESS")
                        return element
                    
        except Exception as e:
            BotFormatter.log(f"Fallback search failed: {e}", "ERROR")
        
        BotFormatter.log("Could not find any input element", "ERROR")
        return None
    
    async def _input_message(self, input_element, message):
        """Input message into the contenteditable element"""
        try:
            BotFormatter.log("Clearing input element", "DEBUG")
            
            # For contenteditable divs, we need to clear differently
            try:
                # Try to clear the content
                input_element.clear()
            except:
                # If clear() doesn't work, try selecting all and deleting
                try:
                    input_element.send_keys(Keys.CONTROL + "a")
                    await asyncio.sleep(0.1)
                    input_element.send_keys(Keys.DELETE)
                except:
                    # Last resort: set innerHTML to empty
                    self.driver.execute_script("arguments[0].innerHTML = '';", input_element)
            
            await asyncio.sleep(0.3)
            
            BotFormatter.log("Clicking input element", "DEBUG")
            input_element.click()
            await asyncio.sleep(0.3)
            
            BotFormatter.log(f"Typing message: {message[:50]}...", "DEBUG")
            
            # Method 1: Try send_keys (works best with contenteditable)
            try:
                input_element.send_keys(message)
                await asyncio.sleep(0.5)
                
                # Verify the text was entered
                entered_text = input_element.text or input_element.get_attribute('innerHTML')
                if message[:20] in entered_text:
                    BotFormatter.log("Message typed successfully with send_keys", "DEBUG")
                    return
                else:
                    BotFormatter.log("send_keys didn't work properly, trying alternatives", "DEBUG")
                    
            except Exception as e:
                BotFormatter.log(f"send_keys failed: {e}, trying JavaScript", "DEBUG")
            
            # Method 2: JavaScript innerHTML
            try:
                # Clear and set content using JavaScript
                self.driver.execute_script("""
                    arguments[0].innerHTML = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, input_element, message)
                await asyncio.sleep(0.5)
                BotFormatter.log("Message typed successfully with JavaScript innerHTML", "DEBUG")
                return
            except Exception as e:
                BotFormatter.log(f"JavaScript innerHTML failed: {e}", "DEBUG")
            
            # Method 3: JavaScript textContent
            try:
                self.driver.execute_script("""
                    arguments[0].textContent = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                """, input_element, message)
                await asyncio.sleep(0.5)
                BotFormatter.log("Message typed successfully with JavaScript textContent", "DEBUG")
                return
            except Exception as e:
                BotFormatter.log(f"JavaScript textContent failed: {e}", "DEBUG")
            
            # Method 4: Focus and type character by character
            try:
                BotFormatter.log("Trying character-by-character typing", "DEBUG")
                input_element.click()
                await asyncio.sleep(0.2)
                
                for char in message:
                    input_element.send_keys(char)
                    await asyncio.sleep(0.01)
                    
                await asyncio.sleep(0.3)
                BotFormatter.log("Character-by-character typing completed", "DEBUG")
                return
                
            except Exception as e:
                BotFormatter.log(f"Character-by-character typing failed: {e}", "ERROR")
                raise
            
        except Exception as e:
            BotFormatter.log(f"All input methods failed: {e}", "ERROR")
            raise
    
    async def _submit_message(self, input_element):
        """Submit the message"""
        try:
            BotFormatter.log("Attempting to submit message with Enter key", "DEBUG")
            input_element.send_keys(Keys.RETURN)
            await asyncio.sleep(1)
            BotFormatter.log("Message submitted with Enter key", "DEBUG")
            return
        except Exception as e:
            BotFormatter.log(f"Enter key failed: {e}, trying submit button", "DEBUG")
        
        # Try finding submit button
        submit_selectors = [
            "button[aria-label*='Send']",
            "button[data-testid*='send']", 
            "button[type='submit']",
            "[role='button'][aria-label*='Send']"
        ]
        
        for selector in submit_selectors:
            try:
                BotFormatter.log(f"Trying submit selector: {selector}", "DEBUG")
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    submit_btn.click()
                    await asyncio.sleep(1)
                    BotFormatter.log(f"Message submitted with button: {selector}", "DEBUG")
                    return
            except Exception as e:
                BotFormatter.log(f"Submit selector {selector} failed: {e}", "DEBUG")
                continue
        
        # Fallback: try Ctrl+Enter
        try:
            BotFormatter.log("Trying Ctrl+Enter fallback", "DEBUG")
            input_element.send_keys(Keys.CONTROL + Keys.RETURN)
            await asyncio.sleep(1)
            BotFormatter.log("Message submitted with Ctrl+Enter", "DEBUG")
        except Exception as e:
            BotFormatter.log(f"Ctrl+Enter failed: {e}", "ERROR")
            # Just continue, maybe the message was sent anyway
    
    async def _wait_for_response(self):
        """Wait for and extract response - based on actual HTML structure"""
        BotFormatter.log("Waiting for Gemini response...", "DEBUG")
        await asyncio.sleep(4)  # Wait for response to appear
        
        max_attempts = 6
        for attempt in range(max_attempts):
            BotFormatter.log(f"Looking for response - attempt {attempt + 1}/{max_attempts}", "DEBUG")
            
            try:
                # Based on your HTML structure, try these selectors in order:
                selectors_to_try = [
                    # The actual structure from your screenshot
                    "message-content.model-response-text p",
                    "message-content.model-response-text div.markdown p", 
                    ".model-response-text p",
                    ".model-response-text div p",
                    
                    # Fallback selectors
                    "div.markdown p:last-child",
                    "div[class*='markdown'] p:last-child",
                    ".markdown-main-panel p",
                    
                    # Even more general fallbacks
                    "message-content p",
                    "p:last-of-type"
                ]
                
                for i, selector in enumerate(selectors_to_try):
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        BotFormatter.log(f"Selector '{selector}' found {len(elements)} elements", "DEBUG")
                        
                        if elements:
                            # Check the last few elements
                            for element in reversed(elements[-3:]):
                                text = element.text.strip()
                                
                                # Check if this looks like a valid response
                                if (text and 
                                    len(text) > 5 and
                                    not text.lower().startswith("important system") and
                                    not text.lower().startswith("you must respond") and
                                    not "Ask Gemini" in text and
                                    not "gemini can make mistakes" in text.lower() and
                                    not text.lower().startswith("the user data directory") and  # Filter out Chrome messages
                                    element.is_displayed()):
                                    
                                    BotFormatter.log(f"Found response with selector '{selector}': {text[:100]}...", "SUCCESS")
                                    return text
                    except Exception as e:
                        BotFormatter.log(f"Selector '{selector}' failed: {e}", "DEBUG")
                        continue
                        
            except Exception as e:
                BotFormatter.log(f"Error in attempt {attempt + 1}: {e}", "DEBUG")
            
            # Wait before next attempt
            await asyncio.sleep(2)
        
        BotFormatter.log("Could not extract response text", "ERROR")
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
    
    async def test_browser_connection(self):
        """Test if browser can connect to Gemini properly"""
        try:
            if not self.is_initialized:
                success = await self.initialize()
                if not success:
                    return "❌ Browser failed to initialize"
            
            # Navigate to Gemini
            BotFormatter.log("Testing browser connection to Gemini", "DEBUG")
            self.driver.get(self.gemini_url)
            await asyncio.sleep(5)
            
            # Check page title
            page_title = self.driver.title
            BotFormatter.log(f"Page title: {page_title}", "DEBUG")
            
            # Check for sign-in requirements
            sign_in_elements = self.driver.find_elements(By.CSS_SELECTOR, "[href*='signin'], [href*='login']")
            if sign_in_elements:
                return f"⚠️ Sign-in required. Page: {page_title}"
            
            # Try to find input element
            input_element = await self._find_input_element()
            if input_element:
                return f"✅ Browser ready! Page: {page_title}"
            else:
                return f"❌ No input found. Page: {page_title}"
                
        except Exception as e:
            return f"❌ Browser test failed: {str(e)[:50]}..."
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                BotFormatter.log("Advanced browser closed", "BROWSER")
            except:
                pass
            self.driver = None
            self.is_initialized = False