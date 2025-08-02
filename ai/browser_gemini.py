#!/usr/bin/env python3
"""
Browser-based Gemini AI integration
"""

import asyncio
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
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Windows API for clipboard
try:
    import win32clipboard
    WIN32_CLIPBOARD_AVAILABLE = True
except ImportError:
    WIN32_CLIPBOARD_AVAILABLE = False


class BrowserGemini:
    """Browser-based Gemini AI integration"""
    
    def __init__(self, browser_type="chrome", headless=False):
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None
        self.gemini_url = "https://gemini.google.com/"
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the browser and navigate to Gemini"""
        if not SELENIUM_AVAILABLE:
            BotFormatter.log("Selenium not available. Install with: pip install selenium", "ERROR")
            return False
        
        try:
            BotFormatter.log("Initializing browser for Gemini...", "BROWSER")
            
            # Setup Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1200,800")
            
            # Try to use existing Chrome profile to avoid login
            chrome_options.add_argument("--user-data-dir=C:/temp/chrome_bot_profile")
            
            # Initialize the driver
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to Gemini
            BotFormatter.log("Opening Gemini in browser...", "BROWSER")
            self.driver.get(self.gemini_url)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            self.is_initialized = True
            BotFormatter.log("Browser Gemini initialized successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            BotFormatter.log(f"Failed to initialize browser: {e}", "ERROR")
            BotFormatter.log("Make sure Chrome is installed and chromedriver is in PATH", "ERROR")
            return False
    
    async def ask_question(self, question):
        """Ask a question to Gemini via browser automation"""
        if not self.is_initialized:
            if not await self.initialize():
                return "❌ Browser not available"
        
        # Enhanced prompt for better responses
        enhanced_prompt = self._create_enhanced_prompt(question)

        try:
            BotFormatter.log(f"Asking Gemini: {question}", "BROWSER")
            
            # Find the input box (try multiple selectors)
            input_selectors = [
                "textarea[placeholder*='Enter a prompt']",
                "textarea[data-testid='textbox']",
                "textarea",
                ".ql-editor",
                "[contenteditable='true']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not input_element:
                return "❌ Could not find input box on Gemini page"
            
            # Clear any existing text and input the enhanced prompt
            input_element.clear()
            await asyncio.sleep(0.2)
            input_element.send_keys(enhanced_prompt)
            await asyncio.sleep(0.2)
            
            # Submit the question (try Enter key first, then find submit button)
            try:
                input_element.send_keys(Keys.RETURN)
                BotFormatter.log("Question submitted via Enter key", "BROWSER")
            except:
                # Try to find and click submit button
                submit_selectors = [
                    "button[type='submit']",
                    "button[aria-label*='Send']",
                    "button[data-testid='send-button']",
                    ".send-button"
                ]
                
                for selector in submit_selectors:
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        submit_btn.click()
                        BotFormatter.log("Question submitted via button click", "BROWSER")
                        break
                    except:
                        continue
            
            # Wait for response (look for new content)
            BotFormatter.log("Waiting for Gemini response...", "BROWSER")
            await asyncio.sleep(3)  # Give time for response to start
            
            # Try to get the response text
            response_selectors = [
                "[data-testid='response']",
                ".response-content",
                ".model-response",
                ".markdown",
                "div[data-testid] p",
                ".conversation-turn p"
            ]
            
            response_text = ""
            for selector in response_selectors:
                try:
                    response_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if response_elements:
                        # Get the last response (most recent)
                        response_text = response_elements[-1].text.strip()
                        if response_text and len(response_text) > 10:  # Valid response
                            break
                except:
                    continue
            
            # If we couldn't get response via selectors, try copying page content
            if not response_text and WIN32_CLIPBOARD_AVAILABLE:
                try:
                    # Try to select and copy the response
                    self.driver.execute_script("window.getSelection().selectAllChildren(document.body);")
                    await asyncio.sleep(0.5)
                    
                    # Copy to clipboard
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.CONTROL + "c")
                    await asyncio.sleep(0.5)
                    
                    # Get from clipboard
                    win32clipboard.OpenClipboard()
                    try:
                        clipboard_content = win32clipboard.GetClipboardData()
                        # Extract response from clipboard content (simple approach)
                        lines = clipboard_content.split('\n')
                        for i, line in enumerate(lines):
                            if enhanced_prompt.lower() in line.lower() and i + 1 < len(lines):
                                response_text = lines[i + 1].strip()
                                break
                    finally:
                        win32clipboard.CloseClipboard()
                        
                except Exception as e:
                    BotFormatter.log(f"Clipboard method failed: {e}", "DEBUG")
            
            if response_text:
                BotFormatter.log(f"Got Gemini response: {response_text[:100]}...", "BROWSER")
                return response_text
            else:
                return "❌ Could not get response from Gemini"
                
        except Exception as e:
            BotFormatter.log(f"Error asking Gemini: {e}", "ERROR")
            return f"❌ Browser error: {str(e)[:50]}..."
    
    def _create_enhanced_prompt(self, user_question):
        """Create an enhanced prompt for better Gemini responses"""
        
        # Detect the language of the question to respond in the same language
        if self._is_arabic_text(user_question):
            language_instruction = "Respond in Arabic (Darija/Moroccan Arabic) using Arabic script."
        elif self._is_french_text(user_question):
            language_instruction = "Respond in French."
        elif self._contains_darija(user_question):
            language_instruction = "Respond in Moroccan Darija using Latin script (like: 'Salam, kifach nta?')."
        else:
            language_instruction = "Respond in the same language as the question."
        
        enhanced_prompt = f"""You are a helpful, friendly AI assistant in a game chat. 

{language_instruction}

Guidelines for your response:
- Keep responses conversational and engaging
- Use appropriate tone for the context
- If it's a game-related question, be enthusiastic
- For general questions, be helpful and informative
- For casual chat, be friendly and fun
- Maximum 200 characters when possible for chat readability
- Use emojis sparingly and appropriately
- Be natural and human-like in your responses

User's question: {user_question}

Remember: respond naturally as if you're chatting with a friend in a game!"""

        return enhanced_prompt
    
    def _is_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        arabic_chars = set('ابتثجحخدذرزسشصضطظعغفقكلمنهوىي')
        return any(char in arabic_chars for char in text)
    
    def _is_french_text(self, text):
        """Check if text appears to be French"""
        french_words = ['bonjour', 'salut', 'comment', 'ça va', 'merci', 'oui', 'non', 'avec', 'dans', 'pour', 'que', 'qui', 'mais', 'tout', 'bien']
        text_lower = text.lower()
        return any(word in text_lower for word in french_words)
    
    def _contains_darija(self, text):
        """Check if text contains Moroccan Darija in Latin script"""
        darija_words = ['kifach', 'kif', 'shno', 'fin', 'wash', 'wach', 'aji', 'makayn', 'kayn', 'bghit', 'bghiti', 'ana', 'nta', 'nti', 'hna']
        text_lower = text.lower()
        return any(word in text_lower for word in darija_words)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                BotFormatter.log("Browser closed", "BROWSER")
            except:
                pass
            self.driver = None
            self.is_initialized = False