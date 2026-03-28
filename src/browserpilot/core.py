import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import ollama
from common.settings import load_settings

SESSION_FILE = Path(".browserpilot_session.json")

class BrowserPilot:
    def __init__(self):
        pass

    def _get_app_data(self):
        if SESSION_FILE.exists():
            return json.loads(SESSION_FILE.read_text())
        return {}

    def _run_with_page(self, callback):
        data = self._get_app_data()
        cdp_url = data.get("cdp_url")
        if not cdp_url:
            raise Exception("Browser not started. Run 'start' first.")
        
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            # Find or create context/page
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            
            result = callback(page)
            # We don't close the browser here, just disconnect
            return result

    def open(self, url):
        def _task(page):
            page.goto(url)
            print(f"Opened {url}")
        return self._run_with_page(_task)

    def click(self, selector):
        def _task(page):
            page.click(selector)
            print(f"Clicked {selector}")
        return self._run_with_page(_task)

    def js(self, script):
        def _task(page):
            result = page.evaluate(script)
            print(result)
            return result
        return self._run_with_page(_task)

    def screenshot(self, path):
        def _task(page):
            page.screenshot(path=path)
            print(f"Screenshot saved to {path}")
        return self._run_with_page(_task)

    def ai_click(self, description):
        def _task(page):
            # Extract interactive elements for context
            elements_data = page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('button, a, input, [role="button"]'));
                    return elements.map(el => ({
                        tag: el.tagName,
                        text: el.innerText || el.value || el.placeholder,
                        id: el.id,
                        class: el.className,
                        selector: el.id ? `#${el.id}` : el.tagName.toLowerCase() + (el.className ? `.${el.className.split(' ').join('.')}` : '')
                    })).filter(e => e.text && e.text.trim().length > 0);
                }
            """)
            
            prompt = f"Given these interactive elements on a web page:\n{json.dumps(elements_data[:50])}\n\nWhich one best matches the description: '{description}'? Return ONLY the CSS selector of that element."
            
            settings = load_settings()
            model = settings.get("ollama_model", "llama3")
            
            response = ollama.chat(model=model, messages=[
                {'role': 'system', 'content': 'You are a browser automation assistant. Return only a valid CSS selector.'},
                {'role': 'user', 'content': prompt},
            ])
            
            selector = response['message']['content'].strip().split('\n')[0].replace('`', '')
            print(f"AI suggests selector: {selector}")
            page.click(selector)
            return selector

        return self._run_with_page(_task)

    def ai_query(self, prompt):
        def _task(page):
            # Extract text content
            text_content = page.evaluate("document.body.innerText")
            
            full_prompt = f"Context from the current web page:\n{text_content[:4000]}\n\nUser Question: {prompt}"
            
            settings = load_settings()
            model = settings.get("ollama_model", "llama3")
            
            response = ollama.chat(model=model, messages=[
                {'role': 'user', 'content': full_prompt},
            ])
            
            answer = response['message']['content']
            print(f"AI Answer: {answer}")
            return answer

        return self._run_with_page(_task)

    def stop(self):
        # Stop is handled by the CLI usually, but for consistency:
        data = self._get_app_data()
        cdp_url = data.get("cdp_url")
        if cdp_url:
             with sync_playwright() as p:
                try:
                    browser = p.chromium.connect_over_cdp(cdp_url)
                    browser.close()
                except:
                    pass
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        print("Browser session stopped.")
