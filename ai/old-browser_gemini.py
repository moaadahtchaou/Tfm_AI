#!/usr/bin/env python3
"""
Fixed Browser-based Gemini AI integration with your Chrome profile
REPLACE: ai/browser_gemini.py
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

# Windows API for clipboard
try:
    import win32clipboard
    WIN32_CLIPBOARD_AVAILABLE = True
except ImportError:
    WIN32_CLIPBOARD_AVAILABLE = False


class BrowserGemini:
    """Browser-based Gemini AI integration with your Chrome profile"""
    
    def __init__(self, browser_type="chrome", headless=False):
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None
        self.gemini_url = "https://gemini.google.com/"
        self.is_initialized = False
        self.last_response_count = 0
        
        # Your specific Chrome profile path
        self.chrome_profile_path = r"C:\Users\moaad\AppData\Local\Google\Chrome\User Data\Profile 2"
        
    async def initialize(self):
        """Initialize the browser and navigate to Gemini"""
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
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # Try to find the input box to confirm we're on the right page
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.find_element(By.TAG_NAME, "textarea") or 
                                  driver.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
                )
                BotFormatter.log("Gemini page loaded successfully!", "SUCCESS")
            except TimeoutException:
                BotFormatter.log("Warning: Gemini input not found - may need manual login", "WARNING")
            
            self.is_initialized = True
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
        
        # Create enhanced prompt
        enhanced_prompt = self._create_enhanced_prompt(question)

        try:
            BotFormatter.log(f"Asking Gemini: {question}", "BROWSER")
            
            # Count existing responses before asking
            self.last_response_count = self._count_existing_responses()
            
            # Find the input box
            input_element = await self._find_input_element()
            if not input_element:
                return "❌ Could not find input box on Gemini page"
            
            # Input the enhanced prompt
            await self._input_question(input_element, enhanced_prompt)
            
            # Submit the question
            await self._submit_question(input_element)
            
            # Wait for and extract the response
            response = await self._wait_for_and_extract_response()
            
            if response:
                BotFormatter.log(f"Got Gemini response: {response[:100]}...", "BROWSER")
                return response
            else:
                return "❌ Could not get response from Gemini"
                
        except Exception as e:
            BotFormatter.log(f"Error asking Gemini: {e}", "ERROR")
            return f"❌ Browser error: {str(e)[:50]}..."
    
    def _count_existing_responses(self):
        """Count existing response elements"""
        try:
            response_selectors = [
                "[data-test-id*='conversation-turn']",
                "[data-test-id*='model-turn']",
                ".model-response-text",
                "article",
            ]
            
            for selector in response_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return len(elements)
                except:
                    continue
            
            return 0
        except:
            return 0
    
    async def _find_input_element(self):
        """Find the input element"""
        input_selectors = [
            "textarea[placeholder*='Enter a prompt']",
            "textarea[placeholder*='Ask Gemini']",
            "textarea",
            "[contenteditable='true']",
            "[role='textbox']"
        ]
        
        for selector in input_selectors:
            try:
                input_element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return input_element
            except TimeoutException:
                continue
        
        return None
    
    async def _input_question(self, input_element, question):
        """Input the question into the element"""
        try:
            input_element.clear()
            await asyncio.sleep(0.3)
            input_element.click()
            await asyncio.sleep(0.2)
            
            # Try send_keys first
            try:
                input_element.send_keys(question)
                await asyncio.sleep(0.3)
                return
            except Exception as e:
                BotFormatter.log(f"send_keys failed: {e}", "DEBUG")
            
            # Fallback to JavaScript
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                input_element, question
            )
            await asyncio.sleep(0.3)
            
        except Exception as e:
            BotFormatter.log(f"Input failed: {e}", "ERROR")
            raise
    
    async def _submit_question(self, input_element):
        """Submit the question"""
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
    
    async def _wait_for_and_extract_response(self):
        """Wait for response and extract it"""
        BotFormatter.log("Waiting for Gemini response...", "BROWSER")
        
        # Wait for response to start appearing
        max_wait_time = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            current_count = self._count_existing_responses()
            if current_count > self.last_response_count:
                break
            await asyncio.sleep(1)
        
        # Wait for response to fully load
        await asyncio.sleep(3)
        
        # Extract the response
        response = await self._extract_response_text()
        return response
    
    async def _extract_response_text(self):
        """Extract response text using multiple methods"""
        # Method 1: Try CSS selectors
        response_selectors = [
            "article:last-child",
            "[data-test-id*='conversation-turn']:last-child",
            ".model-response-text:last-child"
        ]
        
        for selector in response_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    text = elements[-1].text.strip()
                    if text and len(text) > 5:
                        return text
            except:
                continue
        
        return None
    
    def _create_enhanced_prompt(self, user_question):
        """Create an enhanced prompt for better Gemini responses"""
        
        # Detect the language
        if self._is_arabic_text(user_question):
            language_instruction = "respond in Arabic"
        elif self._is_french_text(user_question):
            language_instruction = "respond in French"
        elif self._contains_darija(user_question):
            language_instruction = "respond in Moroccan Darija"
        else:
            language_instruction = "respond in the same language as the question"
        
        # Create a single-line prompt
        enhanced_prompt = f"You are a helpful, friendly AI assistant in a game chat. {language_instruction.capitalize()} in a conversational and engaging way. Keep responses under 200 characters when possible for chat readability. Use emojis sparingly and appropriately. Be natural and human-like. User's question: {user_question} Remember: respond naturally as if you're chatting with a friend in a game!"
        
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