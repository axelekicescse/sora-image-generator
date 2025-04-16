"""
Main executable script for generating images from text prompts using Sora.
This script orchestrates the entire image generation process:
1. Reads prompt from prompt.txt
2. Authenticates with sora.com using session.json
3. Submits the prompt and waits for image generation
4. Downloads and saves the generated image
5. Logs the entire process
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright

import sora_utils

def read_prompt(prompt_file: Optional[str] = None) -> Optional[str]:
    """
    Read the prompt from the prompt.txt file.
    
    Args:
        prompt_file: Path to the prompt file
        
    Returns:
        The prompt text or None if file is missing or empty
    """
    if prompt_file is None:
        prompt_file = "prompt.txt"
        
    try:
        if not os.path.exists(prompt_file):
            return None
            
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
            
        if not prompt:
            return None
            
        return prompt
        
    except Exception as e:
        print(f"Error reading prompt file: {str(e)}")
        return None

def load_session(session_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load the session data from session.json.
    
    Args:
        session_file: Path to the session file
        
    Returns:
        Session data dictionary or None if file is missing
    """
    if session_file is None:
        session_file = "session.json"
        
    try:
        if not os.path.exists(session_file):
            return None
            
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)
            
        return session_data
        
    except Exception as e:
        print(f"Error loading session file: {str(e)}")
        return None

def main():
    config = sora_utils.CONFIG
    
    logger = sora_utils.setup_logging()
    logger.info("Starting Sora image generation process")
    
    timeout = int(config["MAX_SESSION_TIME"])
    sora_utils.setup_global_timeout(timeout, logger)
    
    start_time = time.time()
    
    prompt = read_prompt()
    if not prompt:
        logger.error("Missing or empty prompt.txt file")
        sora_utils.log_session_result(
            logger, 
            prompt="N/A", 
            status="FAILURE", 
            error="Missing or empty prompt.txt file"
        )
        sys.exit(1)
    
    logger.info(f"Read prompt: \"{prompt}\"")
    
    session_data = load_session()
    if not session_data:
        logger.error("Missing session.json file")
        sora_utils.log_session_result(
            logger, 
            prompt=prompt, 
            status="FAILURE", 
            error="Missing session.json file. Please login manually to sora.com and export session.json."
        )
        sys.exit(1)
    
    logger.info("Session data loaded successfully")
    
    image_path = sora_utils.generate_image_filename(prompt)
    
    with sync_playwright() as p:
        try:
            logger.info("Launching browser")
            headless = config["HEADLESS"].lower() == "true"
            
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )
            
            # Process cookies from session.json
            logger.info("Processing cookies from session.json")
            cookies = session_data.get("cookies", [])
            processed_cookies = []
            
            for cookie in cookies:
                processed_cookie = cookie.copy()
                
                if "sameSite" in processed_cookie:
                    if processed_cookie["sameSite"] == "no_restriction":
                        processed_cookie["sameSite"] = "None"
                    elif processed_cookie["sameSite"] == "lax":
                        processed_cookie["sameSite"] = "Lax"
                    elif processed_cookie["sameSite"] == "strict":
                        processed_cookie["sameSite"] = "Strict"
                
                for key in list(processed_cookie.keys()):
                    if key not in ["name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"]:
                        del processed_cookie[key]
                
                if "expirationDate" in processed_cookie:
                    processed_cookie["expires"] = processed_cookie.pop("expirationDate")
                
                processed_cookies.append(processed_cookie)
            
            logger.info(f"Adding {len(processed_cookies)} processed cookies to browser context")
            context.add_cookies(processed_cookies)
            
            # Apply storage state if available
            if "origins" in session_data and session_data["origins"]:
                logger.info("Setting storage state from session.json")
                
                for origin in session_data.get("origins", []):
                    origin_url = origin.get("origin")
                    if origin_url and "sora" in origin_url:
                        logger.info(f"Setting storage for origin: {origin_url}")
                        
                        if "localStorage" in origin:
                            page = context.new_page()
                            page.goto(origin_url)
                            for item in origin.get("localStorage", []):
                                page.evaluate("""([key, value]) => {
                                    localStorage.setItem(key, value);
                                }""", [item.get("name"), item.get("value")])
                            page.close()
                            
                        if "sessionStorage" in origin:
                            page = context.new_page()
                            page.goto(origin_url)
                            for item in origin.get("sessionStorage", []):
                                page.evaluate("""([key, value]) => {
                                    sessionStorage.setItem(key, value);
                                }""", [item.get("name"), item.get("value")])
                            page.close()
            
            page = context.new_page()
            
            page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "sec-ch-ua": '"Chromium";v="123", "Google Chrome";v="123", "Not:A-Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            })
            
            logger.info(f"Navigating to {config['SORA_URL']}")
            page.goto(config["SORA_URL"], wait_until="domcontentloaded")
            
            if not sora_utils.verify_navigation(page, logger, config["SORA_URL"]):
                logger.error("Navigation to Sora website failed")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Navigation to Sora website failed"
                )
                browser.close()
                sys.exit(1)
            
            logger.info("Using JavaScript to interact with the page")
            
            time.sleep(10)
            
            screenshot_path = "debug_screenshot.png"
            logger.info(f"Taking screenshot to debug page state: {screenshot_path}")
            page.screenshot(path=screenshot_path)
            
            html_content = page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("Saved page HTML content to debug_page.html")
            
            js_errors = page.evaluate("""() => {
                return window.errors || [];
            }""")
            if js_errors:
                logger.warning(f"JavaScript errors on page: {js_errors}")
            
            logger.info("Attempting to find input elements using JavaScript")
            has_input = page.evaluate("""() => {
                const inputs = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
                console.log('Found inputs:', inputs.length);
                return inputs.length > 0;
            }""")
            
            if not has_input:
                logger.error("Could not find any input elements using JavaScript")
                logger.info("Trying to wait longer for page to load completely...")
                time.sleep(30)  # Wait longer for page to load
                
                has_input = page.evaluate("""() => {
                    const inputs = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
                    console.log('Found inputs after waiting:', inputs.length);
                    return inputs.length > 0;
                }""")
                
                if not has_input:
                    logger.error("Still could not find any input elements after waiting")
                    sora_utils.log_session_result(
                        logger, 
                        prompt=prompt, 
                        status="FAILURE", 
                        error="Could not find any input elements using JavaScript"
                    )
                    browser.close()
                    sys.exit(1)
                
            logger.info("Entering prompt text using JavaScript")
            page.evaluate(f"""(prompt) => {{
                const inputs = document.querySelectorAll('textarea, input[type="text"]');
                if (inputs.length > 0) {{
                    inputs[0].value = prompt;
                    inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}""", prompt)
            
            logger.info("Clicking generate button using JavaScript")
            button_clicked = page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const generateButton = buttons.find(button => 
                    button.textContent.toLowerCase().includes('generate') || 
                    button.innerText.toLowerCase().includes('generate')
                );
                
                if (generateButton) {
                    generateButton.click();
                    return true;
                }
                return false;
            }""")
            
            if not button_clicked:
                logger.error("Could not find or click the generate button")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Could not find or click the generate button"
                )
                browser.close()
                sys.exit(1)
            
            time.sleep(1)  # Short delay to allow immediate errors to appear
            has_error, error_message = sora_utils.check_for_errors(page, logger)
            if has_error:
                logger.error(f"Error detected immediately after clicking generate: {error_message}")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error=f"Error detected immediately after clicking generate: {error_message}"
                )
                browser.close()
                sys.exit(1)
            
            if not sora_utils.wait_for_image_generation(page, logger):
                logger.error("Image generation failed or timed out")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Image generation failed or timed out"
                )
                browser.close()
                sys.exit(1)
            
            try:
                if not sora_utils.download_image(page, image_path, logger):
                    logger.error("Failed to download the generated image after retries")
                    sora_utils.log_session_result(
                        logger, 
                        prompt=prompt, 
                        status="FAILURE", 
                        error="Failed to download the generated image after retries"
                    )
                    browser.close()
                    sys.exit(1)
            except Exception as e:
                logger.error(f"Error downloading image: {str(e)}")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error=f"Error downloading image: {str(e)}"
                )
                browser.close()
                sys.exit(1)
            
            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = timeout - elapsed_time
            
            if remaining_time < 30:  # Less than 30 seconds remaining
                logger.warning(f"Approaching global timeout limit. Only {remaining_time:.1f}s remaining of {timeout}s")
            
            sora_utils.log_session_result(
                logger, 
                prompt=prompt, 
                status="SUCCESS", 
                file_path=image_path, 
                elapsed_time=elapsed_time
            )
            
            logger.info("Image generation process completed successfully")
            browser.close()
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            sora_utils.log_session_result(
                logger, 
                prompt=prompt, 
                status="FAILURE", 
                error=f"Unexpected error: {str(e)}"
            )
            sys.exit(1)

if __name__ == "__main__":
    main()
