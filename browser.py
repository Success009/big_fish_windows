# browser.py - The Bridge (Clipboard-Fixed & High-Speed Edition)
import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright, TimeoutError

# --- CLIPBOARD AUTO-INSTALLER ---
try:
    import pyperclip
except ImportError:
    print("\n[System] Installing 'pyperclip' for high-speed clipboard functionality...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"], stdout=subprocess.DEVNULL)
        import pyperclip
    except Exception as e:
        print(f"[System] Failed to install pyperclip: {e}")
# --------------------------------

class BrowserClosedError(Exception): pass

class AIStudioController:
    def __init__(self, cdp_url="http://localhost:9222"):
        self.cdp_url = cdp_url
        self.playwright = sync_playwright().start()
        self.browser = None
        self.page = None

    def connect(self):
        try:
            if not self.browser or not self.browser.is_connected():
                self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            for _ in range(10): 
                for context in self.browser.contexts:
                    for pg in context.pages:
                        if "aistudio.google.com" in pg.url:
                            self.page = pg
                            self.page.bring_to_front() 
                            try: self.page.evaluate("document.body.style.zoom = '0.25'")
                            except: pass
                            return True
                time.sleep(1)
            raise BrowserClosedError("Could not find the automatically opened AI Studio tab.")
        except Exception as e:
            raise BrowserClosedError(f"Connection failed: {e}")

    def configure_tools_for_prompt(self, enable_url_context=False):
        self.connect()
        if not enable_url_context: return 
        print("\n[Browser] URL detected! Activating URL Context...")
        try:
            tools_btn = self.page.locator('button:has-text("Tools")').last
            if tools_btn.is_visible(timeout=5000): tools_btn.click(force=True); time.sleep(1)
            switch = self.page.get_by_role("switch", name="Browse the url context")
            if switch.is_visible(timeout=2000) and switch.get_attribute('aria-checked') != 'true':
                switch.click(force=True); time.sleep(0.5) 
            self.page.keyboard.press("Escape")
        except Exception: pass

    def load_chat(self, url):
        self.connect()
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2) 
            try: self.page.evaluate("document.body.style.zoom = '0.25'")
            except: pass
        except Exception as e:
            print(f"[Browser] Failed to load chat URL: {e}")

    def start_new_chat(self):
        self.connect()
        try:
            self.page.evaluate("""
                window.onbeforeunload = null; 
                setTimeout(() => { window.location.href = 'https://aistudio.google.com/app/prompts/new_chat'; }, 100);
            """)
            time.sleep(2)
            try: self.page.evaluate("document.body.style.zoom = '0.25'")
            except: pass
        except Exception: pass

    def get_current_url(self):
        self.connect()
        try: return self.page.url
        except: return None

    def get_current_profile(self):
        try:
            js_email = """() => {
                const btn = document.querySelector('[aria-label^="Google Account"]');
                if (btn) {
                    const label = btn.getAttribute('aria-label');
                    const emailMatch = label.match(/\\(([^)]+@[a-zA-Z0-9.-]+)\\)/);
                    if (emailMatch) return emailMatch[1];
                    return label.replace('Google Account:', '').trim().split('\\n')[0];
                }
                return "Unknown Profile";
            }"""
            return self.page.evaluate(js_email)
        except Exception:
            return "Unknown Profile"

    def paste_from_clipboard(self):
        self.connect()
        try:
            chat_box = self.page.locator('textarea,[contenteditable="true"]').last
            chat_box.focus()
            self.page.keyboard.press("Control+v")
            time.sleep(1) 
            try:
                acknowledge_btn = self.page.locator('button:has-text("Acknowledge")').first
                if acknowledge_btn.is_visible(timeout=2000): acknowledge_btn.click(force=True)
            except TimeoutError: pass
            time.sleep(1) 
            return True
        except Exception: return False

    def send_prompt_and_get_response(self, base_prompt, turn_marker):
        self.connect()
        try:
            time.sleep(0.5)
            self.page.keyboard.press("Escape")
            self.page.keyboard.press("Escape")
            
            chat_box = self.page.locator('textarea,[contenteditable="true"]').last
            try: chat_box.wait_for(state="attached", timeout=15000)
            except Exception:
                print("\n" + "="*50)
                print("🚨 BROWSER ACTION REQUIRED 🚨")
                print("Could not find the chat box! Please check Chrome, sign in, and close any popups.")
                print("="*50 + "\n")
                return None
                
            chat_box.click(force=True, timeout=5000)
            time.sleep(0.2)
            
            self.page.evaluate('el => { if(el.textContent !== undefined) el.textContent = ""; else el.value = ""; }', chat_box.element_handle())
            
            try: self.page.evaluate("document.body.style.zoom = '0.25'")
            except: pass
            
            # --- THE CLIPBOARD SPLIT-PAYLOAD INJECTION ---
            try:
                old_clip = ""
                try: old_clip = pyperclip.paste()
                except: pass
                
                # 1. Paste the heavy code (Triggers AI Studio's File Attachment conversion)
                pyperclip.copy(base_prompt)
                self.page.keyboard.press("Control+v")
                time.sleep(0.5) 
                
                # 2. Safely type the marker natively so it stays visible in the DOM
                self.page.keyboard.insert_text(f"\n\n{turn_marker}")
                time.sleep(0.2) 
                
                # 3. Restore the user's original clipboard
                try: pyperclip.copy(old_clip)
                except: pass
                
            except Exception as e:
                print(f"\n[Browser] Clipboard paste failed ({e}). Falling back to standard typing.")
                print("[Browser] Fix: On Linux, you may need to run 'sudo apt install xclip wl-clipboard'")
                self.page.keyboard.insert_text(f"{base_prompt}\n\n{turn_marker}")
                time.sleep(0.2)
            # ---------------------------------------------
            
            self.page.keyboard.press("Control+Enter")
            time.sleep(1.0) 
            
            js_monitor = """() => {
                const text = document.body.textContent || "";
                const marker = "%s";
                const markerIdx = text.lastIndexOf(marker);
                
                if (markerIdx === -1) return { tag_found: false, max_len: 0 };
                
                const newText = text.substring(markerIdx + marker.length);
                const lowerText = newText.toLowerCase();
                
                const tagFound = lowerText.includes("<response>") && lowerText.includes("</response>");
                
                return { tag_found: tagFound, max_len: newText.length };
            }""" % turn_marker
            
            stable_checks, loops = 0, 0
            last_length = 0
            has_started_typing = False
            
            while loops < 1500: 
                time.sleep(0.2) 
                loops += 1
                try:
                    data = self.page.evaluate(js_monitor)
                    
                    if data['tag_found']:
                        print(f"\n[Browser] ⚡ Response END tag detected! (Captured in {loops * 0.2:.1f}s)")
                        break
                        
                    current_length = data['max_len']
                    
                    if current_length > 10:
                        has_started_typing = True
                        
                    if current_length == last_length and current_length > 0:
                        stable_checks += 1
                    else:
                        stable_checks = 0
                        
                    last_length = current_length
                    
                    if has_started_typing and stable_checks >= 50: 
                        print(f"\n[Browser] ⚠️ 10-second UI silence reached. Forcing capture without end tag.")
                        break
                        
                    if not has_started_typing and loops >= 900: 
                        break
                except Exception: pass
            
            try:
                self.page.evaluate("document.querySelectorAll('details').forEach(d => d.setAttribute('open', 'true'))")
                time.sleep(0.1) 
            except Exception: pass
            
            try:
                return self.page.locator("body").inner_text()
            except Exception:
                return self.page.evaluate("document.body.textContent")
                
        except Exception as e:
            print(f"[Browser] CRITICAL ERROR: Could not send prompt. {e}")
            return None

    def close(self):
        if self.playwright: self.playwright.stop()
