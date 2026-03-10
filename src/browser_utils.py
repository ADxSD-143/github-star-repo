from playwright.sync_api import sync_playwright, BrowserContext, Page
import time

class BrowserManager:
    """
    Manages the Playwright browser connection.
    To avoid authentication issues, we recommend connecting to an existing Chrome instance
    launched with debugging enabled:
    `chrome.exe --remote-debugging-port=9222`
    """
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        try:
            print(f"Attempting to connect to existing browser at {self.cdp_url}...")
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # Use the first context
            contexts = self.browser.contexts
            if not contexts:
                print("No context found! Launching new context.")
                context = self.browser.new_context()
            else:
                context = contexts[0]
                
            self.page = context.new_page()
            print("Successfully connected to browser.")
            
        except Exception as e:
            print(f"Failed to connect over CDP: {e}")
            print("Please ensure Chrome is running with --remote-debugging-port=9222")
            print("Fallback: Launching a new temporary browser (You will need to login manually if required).")
            self.browser = self.playwright.chromium.launch(headless=False)
            self.page = self.browser.new_page()

    def navigate(self, url: str):
        if self.page:
            print(f"Navigating to {url}...")
            self.page.goto(url)
            self.page.wait_for_load_state('networkidle')
            time.sleep(1) # Small buffer for rendering

    def stop(self):
        if self.page:
            self.page.close()
        # if we connected over CDP, we might not want to close the whole browser, just our session
        if self.playwright:
            self.playwright.stop()
