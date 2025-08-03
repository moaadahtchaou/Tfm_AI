#!/usr/bin/env python3
"""
COMPLETE FIXED Advanced Browser-based Gemini AI integration
REPLACE: ai/advanced_browser_gemini.py
"""

import asyncio
import time
import re
from html import unescape
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
        """Generate a cleaner, more effective system prompt"""
        
        # Language configurations with cleaner instructions
        language_configs = {
            'darija': {
                'instruction': "Respond in Moroccan Darija using Latin script",
                'style': "casual, friendly Moroccan style",
                'examples': "Use words like: kifach, wach, bghit, makayn, zwina, etc."
            },
            'arabic': {
                'instruction': "Respond in Arabic using Arabic script",
                'style': "natural Arabic conversation",
                'examples': "Use proper Arabic expressions and grammar"
            },
            'french': {
                'instruction': "Respond in French",
                'style': "conversational French",
                'examples': "Natural French expressions and vocabulary"
            },
            'english': {
                'instruction': "Respond in English",
                'style': "casual, friendly English",
                'examples': "Natural English conversation"
            }
        }
        
        # Topic configurations with better personalities
        topic_configs = {
            'anime': {
                'personality': "You're an anime enthusiast who loves discussing anime, manga, and Japanese culture",
                'traits': "knowledgeable about anime series, characters, and storylines",
                'style': "excited and passionate when talking about anime topics"
            },
            'gaming': {
                'personality': "You're a passionate gamer who loves all types of video games",
                'traits': "knowledgeable about games, strategies, and gaming culture",
                'style': "enthusiastic about gaming topics and helpful with game advice"
            },
            'casual': {
                'personality': "You're a friendly, easy-going person who enjoys casual conversation",
                'traits': "good listener, conversational, and interested in everyday topics",
                'style': "relaxed and natural in conversation"
            },
            'tech': {
                'personality': "You're tech-savvy and love discussing technology and programming",
                'traits': "knowledgeable about computers, software, and tech trends",
                'style': "helpful with tech questions and excited about innovations"
            },
            'sports': {
                'personality': "You're a sports fan who loves discussing various sports and teams",
                'traits': "knowledgeable about sports, teams, players, and statistics",
                'style': "enthusiastic about sports topics and current events"
            }
        }
        
        # Get configurations
        lang_config = language_configs.get(self.language, language_configs['english'])
        topic_config = topic_configs.get(self.topic, topic_configs['casual'])
        
        # Build a cleaner, more natural prompt
        prompt_parts = []
        
        # Core personality
        prompt_parts.append(f"You are {self.name}, a helpful AI assistant chatting in a game.")
        prompt_parts.append(f"{topic_config['personality']}.")
        prompt_parts.append(f"You are {topic_config['traits']}.")
        
        # Language instruction
        prompt_parts.append(f"{lang_config['instruction']} in a {lang_config['style']} way.")
        prompt_parts.append(f"{lang_config['examples']}")
        
        # Chat behavior
        prompt_parts.append("Keep responses short and conversational (under 320 characters when possible).")
        prompt_parts.append(f"Be {topic_config['style']}.")
        prompt_parts.append("Use emojis sparingly but appropriately.")
        
        # Custom instructions (if provided)
        if self.custom_instructions.strip():
            prompt_parts.append(f"Additional instructions: {self.custom_instructions}")
        
        # Final instruction
        prompt_parts.append("Respond naturally as if chatting with a friend in a game!")
        
        # Join all parts into a single instruction
        system_prompt = " ".join(prompt_parts)
        
        return system_prompt


class AdvancedBrowserGemini:
    """Advanced Browser-based Gemini AI with multiple personalities - FIXED VERSION"""
    
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
        """Create a new AI personality from command arguments with improved parsing"""
        # Parse arguments with better handling for quoted strings
        language = "english"
        topic = "casual"
        name = None
        custom_instructions = ""
        
        # Convert the arguments into a more parseable format
        # Handle quoted strings properly
        import re
        
        # First, extract quoted strings for --name and --custom
        quoted_pattern = r'--(\w+)\s+"([^"]*)"'
        quoted_matches = re.findall(quoted_pattern, ai_args)
        
        # Remove quoted parts from args for easier parsing
        args_without_quotes = ai_args
        for match in re.finditer(quoted_pattern, ai_args):
            args_without_quotes = args_without_quotes.replace(match.group(0), f'--{match.group(1)} PLACEHOLDER_{match.group(1).upper()}')
        
        # Now parse the remaining arguments
        args = args_without_quotes.strip().split()
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
                
                # Name flag with placeholder or next argument
                elif flag == 'name':
                    if i + 1 < len(args):
                        next_arg = args[i + 1]
                        if next_arg == 'PLACEHOLDER_NAME':
                            # Find the actual quoted value
                            for param, value in quoted_matches:
                                if param == 'name':
                                    name = value
                                    break
                            i += 1  # Skip the placeholder
                        elif not next_arg.startswith('--'):
                            name = next_arg.strip('"\'')
                            i += 1  # Skip the value
                
                # Custom instruction flag with placeholder or next argument
                elif flag == 'custom':
                    if i + 1 < len(args):
                        next_arg = args[i + 1]
                        if next_arg == 'PLACEHOLDER_CUSTOM':
                            # Find the actual quoted value
                            for param, value in quoted_matches:
                                if param == 'custom':
                                    custom_instructions = value
                                    break
                            i += 1  # Skip the placeholder
                        elif not next_arg.startswith('--'):
                            custom_instructions = args[i + 1].strip('"\'')
                            i += 1  # Skip the value
            
            i += 1
        
        # Generate name if not provided
        if not name:
            name = f"{language}_{topic}_{int(time.time() % 10000)}"
        
        # Make sure browser is initialized
        if not self.is_initialized:
            if not await self.initialize():
                return "❌ Failed to start browser"
        
        # Create the personality object
        personality = AIPersonality(name, language, topic, custom_instructions)
        
        BotFormatter.log(f"Creating AI: {name} (Lang: {language}, Topic: {topic}, Custom: '{custom_instructions}')", "AI")
        
        # Try to initialize the personality
        success = await self._initialize_personality(personality)
        if success:
            # Only add to personalities if initialization succeeded
            self.personalities[name] = personality
            self.current_personality = personality
            BotFormatter.log(f"Successfully created AI: {name}", "AI")
            return f"✅ Created AI: {name}"
        else:
            # Don't save failed personalities
            BotFormatter.log(f"Failed to initialize AI: {name}", "ERROR")
            return "❌ Failed to initialize AI"
    
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
        """Enhanced send message method with better response detection"""
        try:
            BotFormatter.log(f"Attempting to send message: {message[:50]}...", "DEBUG")
            
            # Count existing responses before sending
            initial_response_count = self._count_responses()
            BotFormatter.log(f"Initial response count: {initial_response_count}", "DEBUG")
            
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
            
            # Wait for response with improved detection
            response = await self._wait_for_new_response(initial_response_count)
            
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
    
    def _count_responses(self):
        """Count existing response elements more accurately"""
        try:
            # Count multiple types of response indicators
            selectors = [
                "message-content.model-response-text",
                ".model-response-text",
                "[data-test-id*='model-turn']",
                "div.markdown.markdown-main-panel"
            ]
            
            max_count = 0
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    max_count = max(max_count, len(elements))
                except:
                    continue
            
            BotFormatter.log(f"Counted {max_count} existing responses", "DEBUG")
            return max_count
            
        except Exception as e:
            BotFormatter.log(f"Error counting responses: {e}", "DEBUG")
            return 0
    
    async def _wait_for_new_response(self, initial_count):
        """Wait for a new response to appear"""
        BotFormatter.log(f"Waiting for new response (initial count: {initial_count})", "DEBUG")
        
        max_wait_time = 30  # Maximum wait time in seconds
        start_time = time.time()
        
        # First, wait for response to start appearing
        while time.time() - start_time < max_wait_time:
            current_count = self._count_responses()
            
            if current_count > initial_count:
                BotFormatter.log(f"New response detected! Count: {current_count} > {initial_count}", "DEBUG")
                # Wait a bit more for the response to complete
                await asyncio.sleep(3)
                break
                
            await asyncio.sleep(1)
        else:
            BotFormatter.log("No new response detected in time limit", "WARNING")
        
        # Extract the response
        response = await self._wait_for_response()
        return response
    
    async def _find_input_element(self):
        """Find the input element with improved detection based on actual HTML structure"""
        # Based on your HTML, the structure is:
        # <rich-textarea>
        #   <div class="ql-editor textarea new-input-ui ql-blank" contenteditable="true">
        
        selectors = [
            # Most specific based on your HTML structure
            "rich-textarea div.ql-editor[contenteditable='true']",
            "rich-textarea div.textarea[contenteditable='true']", 
            "rich-textarea div.new-input-ui[contenteditable='true']",
            "rich-textarea div[contenteditable='true']",
            
            # Alternative patterns for rich-textarea
            "rich-textarea [contenteditable='true']",
            
            # More general contenteditable selectors
            "div.ql-editor[contenteditable='true']",
            "div.textarea[contenteditable='true']",
            "div.new-input-ui[contenteditable='true']",
            
            # Placeholder-based selectors
            "div[data-placeholder*='Enter a prompt']",
            "div[data-placeholder*='Ask Gemini']",
            "div[aria-label*='Enter a prompt']",
            "div[aria-label*='Ask Gemini']",
            
            # Generic fallbacks
            "[contenteditable='true'][role='textbox']",
            "[contenteditable='true']",
            
            # Textarea fallbacks
            "textarea[placeholder*='Ask Gemini']",
            "textarea[placeholder*='Enter a prompt']",
            "textarea"
        ]
        
        # Wait for page to be ready
        await asyncio.sleep(2)
        
        BotFormatter.log("Searching for input element...", "DEBUG")
        
        for i, selector in enumerate(selectors):
            try:
                BotFormatter.log(f"Trying input selector {i+1}/{len(selectors)}: {selector}", "DEBUG")
                
                # Wait for element to be present and clickable
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Additional validation
                if element.is_displayed() and element.is_enabled():
                    # Check if it's a reasonable input size (not a huge content area)
                    size = element.size
                    location = element.location
                    
                    BotFormatter.log(f"Found element - Size: {size}, Location: {location}", "DEBUG")
                    
                    # Verify it's likely an input field (reasonable dimensions)
                    if size['height'] < 300 and size['width'] > 50:  # Not too big, not too small
                        BotFormatter.log(f"✅ Found valid input element with selector: {selector}", "SUCCESS")
                        
                        # Test if we can interact with it
                        try:
                            element.click()
                            await asyncio.sleep(0.1)
                            BotFormatter.log("✅ Input element is clickable", "SUCCESS")
                            return element
                        except Exception as e:
                            BotFormatter.log(f"Element not clickable: {e}", "DEBUG")
                            continue
                    else:
                        BotFormatter.log(f"Element size not suitable for input: {size}", "DEBUG")
                        continue
                else:
                    BotFormatter.log(f"Element not displayed or enabled", "DEBUG")
                    continue
                    
            except TimeoutException:
                BotFormatter.log(f"Selector timeout: {selector}", "DEBUG")
                continue
            except Exception as e:
                BotFormatter.log(f"Error with selector {selector}: {e}", "DEBUG")
                continue
        
        # If specific selectors fail, try a more thorough search
        BotFormatter.log("Standard selectors failed, trying comprehensive search", "DEBUG")
        
        try:
            # Find all contenteditable elements
            all_contenteditable = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
            BotFormatter.log(f"Found {len(all_contenteditable)} contenteditable elements", "DEBUG")
            
            for element in all_contenteditable:
                try:
                    if element.is_displayed() and element.is_enabled():
                        size = element.size
                        # Look for input-like characteristics
                        if (size['height'] > 20 and size['height'] < 200 and 
                            size['width'] > 100):
                            
                            # Check parent elements for rich-textarea
                            parent_html = self.driver.execute_script(
                                "return arguments[0].parentElement.outerHTML;", element
                            )
                            
                            if "rich-textarea" in parent_html or "input" in parent_html.lower():
                                BotFormatter.log("✅ Found input via comprehensive search", "SUCCESS")
                                element.click()
                                await asyncio.sleep(0.1)
                                return element
                                
                except Exception as e:
                    BotFormatter.log(f"Error checking element: {e}", "DEBUG")
                    continue
                    
        except Exception as e:
            BotFormatter.log(f"Comprehensive search failed: {e}", "DEBUG")
        
        # Final attempt using JavaScript
        BotFormatter.log("Trying JavaScript-based detection", "DEBUG")
        try:
            input_element = self.driver.execute_script("""
                // Look for rich-textarea specifically
                var richTextarea = document.querySelector('rich-textarea');
                if (richTextarea) {
                    var editableDiv = richTextarea.querySelector('div[contenteditable="true"]');
                    if (editableDiv) {
                        return editableDiv;
                    }
                }
                
                // Fallback: find any contenteditable that looks like input
                var editables = document.querySelectorAll('div[contenteditable="true"]');
                for (var i = 0; i < editables.length; i++) {
                    var rect = editables[i].getBoundingClientRect();
                    if (rect.height > 20 && rect.height < 200 && rect.width > 100) {
                        return editables[i];
                    }
                }
                
                return null;
            """)
            
            if input_element:
                BotFormatter.log("✅ Found input element via JavaScript", "SUCCESS")
                input_element.click()
                await asyncio.sleep(0.1)
                return input_element
                
        except Exception as e:
            BotFormatter.log(f"JavaScript detection failed: {e}", "DEBUG")
        
        BotFormatter.log("❌ Could not find any suitable input element", "ERROR")
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
        """Wait for and extract response - FIXED version based on actual HTML structure"""
        BotFormatter.log("Waiting for Gemini response...", "DEBUG")
        await asyncio.sleep(4)  # Wait for response to appear
        
        max_attempts = 10
        for attempt in range(max_attempts):
            BotFormatter.log(f"Looking for response - attempt {attempt + 1}/{max_attempts}", "DEBUG")
            
            try:
                # Based on your HTML structure, the response is in:
                # <message-content class="model-response-text ng-star-inserted is-mobile">
                #   <div class="markdown markdown-main-panel stronger enable-updated-hr-color">
                #     <p>Response text here</p>
                #   </div>
                # </message-content>
                
                # Try different selectors based on the actual HTML structure
                selectors_to_try = [
                    # Most specific - based on your exact HTML
                    "message-content.model-response-text .markdown.markdown-main-panel p",
                    "message-content.model-response-text div.markdown p",
                    ".model-response-text .markdown p",
                    
                    # Fallback selectors
                    "message-content .markdown p",
                    ".markdown-main-panel p",
                    "div[class*='markdown'] p",
                    
                    # Even more general
                    ".model-response-text p",
                    "message-content p",
                    
                    # Last resort
                    "[data-test-id*='model-turn'] p",
                    "article p"
                ]
                
                found_response = None
                
                for i, selector in enumerate(selectors_to_try):
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        BotFormatter.log(f"Selector '{selector}' found {len(elements)} elements", "DEBUG")
                        
                        if elements:
                            # Get the last few response elements (most recent)
                            recent_elements = elements[-3:] if len(elements) > 3 else elements
                            
                            for element in reversed(recent_elements):
                                try:
                                    text = element.text.strip()
                                    
                                    # Filter out invalid responses
                                    if self._is_valid_response(text):
                                        BotFormatter.log(f"Found valid response with selector '{selector}': {text[:100]}...", "SUCCESS")
                                        found_response = text
                                        break
                                        
                                except Exception as e:
                                    BotFormatter.log(f"Error extracting text from element: {e}", "DEBUG")
                                    continue
                            
                            if found_response:
                                break
                                
                    except Exception as e:
                        BotFormatter.log(f"Selector '{selector}' failed: {e}", "DEBUG")
                        continue
                
                if found_response:
                    return found_response
                    
            except Exception as e:
                BotFormatter.log(f"Error in attempt {attempt + 1}: {e}", "DEBUG")
            
            # Wait before next attempt, with increasing delay
            await asyncio.sleep(2 + (attempt * 0.5))
        
        # If no response found, try alternative extraction methods
        BotFormatter.log("Standard selectors failed, trying alternative methods", "DEBUG")
        return await self._extract_response_alternative()
    
    def _is_valid_response(self, text):
        """Check if extracted text is a valid response"""
        if not text or len(text) < 3:
            return False
        
        # Filter out common invalid responses
        invalid_patterns = [
            "important system",
            "you must respond",
            "ask gemini",
            "gemini can make mistakes",
            "the user data directory",
            "chrome://",
            "send a message",
            "enter a prompt",
            "choose a",
            "based on",
            "copy code",
            "show more",
            "continue",
            "thinking",
            "loading",
            "please wait"
        ]
        
        text_lower = text.lower()
        for pattern in invalid_patterns:
            if pattern in text_lower:
                return False
        
        # Must contain actual content (not just punctuation/numbers)
        letter_count = len(re.findall(r'[a-zA-Z\u0600-\u06FF\u0750-\u077F]', text))
        if letter_count < 3:
            return False
        
        return True
    
    async def _extract_response_alternative(self):
        """Alternative method to extract response when standard selectors fail"""
        try:
            BotFormatter.log("Trying alternative extraction methods", "DEBUG")
            
            # Method 1: Get all paragraphs and find the most recent non-empty one
            all_paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
            BotFormatter.log(f"Found {len(all_paragraphs)} total paragraphs", "DEBUG")
            
            valid_responses = []
            for p in reversed(all_paragraphs[-10:]):  # Check last 10 paragraphs
                try:
                    text = p.text.strip()
                    if self._is_valid_response(text):
                        valid_responses.append(text)
                except:
                    continue
            
            if valid_responses:
                response = valid_responses[0]  # Most recent valid response
                BotFormatter.log(f"Found response via alternative method: {response[:100]}...", "SUCCESS")
                return response
            
            # Method 2: Try to get page source and parse manually
            BotFormatter.log("Trying page source parsing", "DEBUG")
            page_source = self.driver.page_source
            
            # Look for response patterns in page source
            
            # Pattern for markdown content
            markdown_pattern = r'<div[^>]*class="[^"]*markdown[^"]*"[^>]*>(.*?)</div>'
            markdown_matches = re.findall(markdown_pattern, page_source, re.DOTALL | re.IGNORECASE)
            
            for match in reversed(markdown_matches[-3:]):  # Check last 3 matches
                # Extract text from HTML
                
                # Remove HTML tags
                clean_text = re.sub(r'<[^>]+>', '', match)
                clean_text = unescape(clean_text).strip()
                
                if self._is_valid_response(clean_text):
                    BotFormatter.log(f"Found response via page source: {clean_text[:100]}...", "SUCCESS")
                    return clean_text
            
            # Method 3: JavaScript execution to get content
            BotFormatter.log("Trying JavaScript extraction", "DEBUG")
            try:
                # Execute JavaScript to find response content
                response_text = self.driver.execute_script("""
                    // Find all elements that might contain the response
                    var responseElements = document.querySelectorAll('message-content.model-response-text, .model-response-text, .markdown p, [data-test-id*="model"] p');
                    
                    var validTexts = [];
                    for (var i = 0; i < responseElements.length; i++) {
                        var text = responseElements[i].textContent.trim();
                        if (text.length > 10 && !text.toLowerCase().includes('system') && !text.toLowerCase().includes('gemini can make')) {
                            validTexts.push(text);
                        }
                    }
                    
                    return validTexts.length > 0 ? validTexts[validTexts.length - 1] : null;
                """)
                
                if response_text and self._is_valid_response(response_text):
                    BotFormatter.log(f"Found response via JavaScript: {response_text[:100]}...", "SUCCESS")
                    return response_text
                    
            except Exception as e:
                BotFormatter.log(f"JavaScript extraction failed: {e}", "DEBUG")
            
            BotFormatter.log("All extraction methods failed", "ERROR")
            return None
            
        except Exception as e:
            BotFormatter.log(f"Alternative extraction failed: {e}", "ERROR")
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