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

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

import sora_utils
from stealth_launcher import (
    launch_stealth_browser,
    setup_stealth_page,
    apply_session_state,
    handle_cloudflare_challenge,
    verify_sora_access
)

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
            logger.info("Launching stealth browser")
            headless = config["HEADLESS"].lower() == "true"
            
            browser, context = launch_stealth_browser(
                headless=headless,
                logger=logger
            )
            
            # Apply session state from session.json
            logger.info("Applying session state from session.json")
            if not apply_session_state(context, "session.json", logger):
                logger.error("Failed to apply session state from session.json")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Failed to apply session state from session.json"
                )
                browser.close()
                sys.exit(1)
            
            page = context.new_page()
            page = setup_stealth_page(page, logger)
            
            logger.info(f"Navigating to {config['SORA_URL']}")
            page.goto(config["SORA_URL"], wait_until="domcontentloaded")
            
            if not handle_cloudflare_challenge(page, logger):
                logger.error("Failed to bypass Cloudflare challenge")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Failed to bypass Cloudflare challenge"
                )
                browser.close()
                sys.exit(1)
            
            if not verify_sora_access(page, logger):
                logger.error("Failed to access Sora website - region restriction or other access issue")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Failed to access Sora website - region restriction or other access issue"
                )
                browser.close()
                sys.exit(1)
            
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
            
            time.sleep(5)  # Reduced wait time as stealth mode should load faster
            
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
                // Look for textarea at the bottom of the page (Sora's input)
                const textareas = document.querySelectorAll('textarea');
                const inputs = document.querySelectorAll('input[type="text"]');
                const contentEditables = document.querySelectorAll('[contenteditable="true"]');
                
                console.log('Found textareas:', textareas.length);
                console.log('Found text inputs:', inputs.length);
                console.log('Found contentEditables:', contentEditables.length);
                
                return textareas.length > 0 || inputs.length > 0 || contentEditables.length > 0;
            }""")
            
            if not has_input:
                logger.error("Could not find any input elements using JavaScript")
                logger.info("Trying to wait longer for page to load completely...")
                time.sleep(15)  # Wait longer for page to load, but less than before
                
                has_input = page.evaluate("""() => {
                    const textareas = document.querySelectorAll('textarea');
                    const inputs = document.querySelectorAll('input[type="text"]');
                    const contentEditables = document.querySelectorAll('[contenteditable="true"]');
                    
                    console.log('Found textareas after waiting:', textareas.length);
                    console.log('Found text inputs after waiting:', inputs.length);
                    console.log('Found contentEditables after waiting:', contentEditables.length);
                    
                    return textareas.length > 0 || inputs.length > 0 || contentEditables.length > 0;
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
            input_success = page.evaluate(f"""(prompt) => {{
                // Try multiple input methods
                let inputSuccess = false;
                
                // Method 1: Find textarea (most likely for Sora)
                const textareas = document.querySelectorAll('textarea');
                if (textareas.length > 0) {{
                    textareas[0].value = prompt;
                    textareas[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    console.log('Entered prompt in textarea');
                    inputSuccess = true;
                }}
                
                // Method 2: Find input fields
                if (!inputSuccess) {{
                    const inputs = document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {{
                        inputs[0].value = prompt;
                        inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        console.log('Entered prompt in text input');
                        inputSuccess = true;
                    }}
                }}
                
                // Method 3: Find contentEditable elements
                if (!inputSuccess) {{
                    const contentEditables = document.querySelectorAll('[contenteditable="true"]');
                    if (contentEditables.length > 0) {{
                        contentEditables[0].textContent = prompt;
                        contentEditables[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        console.log('Entered prompt in contentEditable');
                        inputSuccess = true;
                    }}
                }}
                
                return inputSuccess;
            }}""", prompt)
            
            if not input_success:
                logger.error("Failed to enter prompt text")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error="Failed to enter prompt text"
                )
                browser.close()
                sys.exit(1)
            
            logger.info("Looking for submit button (paper plane icon)")
            button_clicked = page.evaluate("""() => {
                // Try multiple button finding strategies
                
                // Strategy 1: Look for paper plane icon (Sora's submit button)
                const paperPlaneButtons = Array.from(document.querySelectorAll('button')).filter(button => {
                    // Check for SVG with paper plane icon
                    const svg = button.querySelector('svg');
                    if (svg) {
                        // Check if it looks like a paper plane icon
                        const paths = svg.querySelectorAll('path');
                        if (paths.length > 0) {
                            return true;
                        }
                    }
                    return false;
                });
                
                if (paperPlaneButtons.length > 0) {
                    console.log('Found paper plane button');
                    paperPlaneButtons[0].click();
                    return true;
                }
                
                // Strategy 2: Look for buttons with specific text
                const textButtons = Array.from(document.querySelectorAll('button')).filter(button => {
                    const text = button.textContent.toLowerCase();
                    return text.includes('generate') || 
                           text.includes('create') || 
                           text.includes('submit') ||
                           text.includes('send');
                });
                
                if (textButtons.length > 0) {
                    console.log('Found text button:', textButtons[0].textContent);
                    textButtons[0].click();
                    return true;
                }
                
                // Strategy 3: Look for buttons next to the textarea
                const textareas = document.querySelectorAll('textarea');
                if (textareas.length > 0) {
                    const textarea = textareas[0];
                    const parent = textarea.parentElement;
                    const buttons = parent.querySelectorAll('button');
                    if (buttons.length > 0) {
                        console.log('Found button next to textarea');
                        buttons[0].click();
                        return true;
                    }
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
