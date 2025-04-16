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
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            
            context.storage_state(state=session_data)
            
            page = context.new_page()
            logger.info(f"Navigating to {config['SORA_URL']}")
            page.goto(config["SORA_URL"])
            
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
            
            try:
                if not sora_utils.wait_for_element(page, "textarea", logger, timeout=30):
                    logger.error("Could not find prompt input field after retries")
                    sora_utils.log_session_result(
                        logger, 
                        prompt=prompt, 
                        status="FAILURE", 
                        error="Could not find prompt input field after retries"
                    )
                    browser.close()
                    sys.exit(1)
            except Exception as e:
                logger.error(f"Error waiting for prompt input field: {str(e)}")
                sora_utils.log_session_result(
                    logger, 
                    prompt=prompt, 
                    status="FAILURE", 
                    error=f"Error waiting for prompt input field: {str(e)}"
                )
                browser.close()
                sys.exit(1)
            
            logger.info("Entering prompt text")
            page.fill("textarea", prompt)
            
            logger.info("Clicking generate button")
            generate_button = page.get_by_role("button", name="Generate")
            generate_button.click()
            
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
