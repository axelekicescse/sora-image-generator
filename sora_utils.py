"""
Utility functions for Sora image generation.
Contains helper functions for browser interactions, DOM manipulation, and error handling.
"""
import os
import time
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Logger instance
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{timestamp}_sora.log")
    
    logger = logging.getLogger("sora_image_generator")
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def generate_image_filename(prompt: str, image_dir: str = "images") -> str:
    """
    Generate a unique filename for the image based on timestamp and prompt hash.
    
    Args:
        prompt: The text prompt used to generate the image
        image_dir: Directory to store images
        
    Returns:
        Full path to the image file
    """
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:6]
    
    filename = f"{timestamp}_{prompt_hash}.png"
    
    return os.path.join(image_dir, filename)

def wait_for_element(page, selector: str, timeout: int = 60, state: str = "visible") -> bool:
    """
    Wait for an element to appear on the page.
    
    Args:
        page: Playwright page object
        selector: CSS or XPath selector
        timeout: Maximum time to wait in seconds
        state: Element state to wait for (visible, hidden, attached, detached)
        
    Returns:
        True if element was found, False if timeout occurred
    """
    try:
        page.wait_for_selector(selector, state=state, timeout=timeout * 1000)
        return True
    except Exception:
        return False

def wait_for_image_generation(page, logger: logging.Logger, timeout: int = 300) -> bool:
    """
    Wait for image generation to complete by checking for the download button.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if image generation completed, False if timeout occurred
    """
    logger.info("Waiting for image generation to complete...")
    start_time = time.time()
    
    download_button_selector = "button:has-text('Download')"
    
    while time.time() - start_time < timeout:
        try:
            if page.is_visible(download_button_selector):
                elapsed_time = time.time() - start_time
                logger.info(f"Image generation completed in {elapsed_time:.1f} seconds")
                return True
            
            error_selector = "text='An error occurred'"
            if page.is_visible(error_selector):
                logger.error("Error detected during image generation")
                return False
                
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Exception while checking image status: {str(e)}")
            time.sleep(2)
    
    logger.error(f"Timeout after {timeout} seconds waiting for image generation")
    return False

def download_image(page, image_path: str, logger: logging.Logger) -> bool:
    """
    Download the generated image.
    
    Args:
        page: Playwright page object
        image_path: Path where the image should be saved
        logger: Logger instance
        
    Returns:
        True if download was successful, False otherwise
    """
    try:
        logger.info(f"Downloading image to {image_path}")
        
        download_button_selector = "button:has-text('Download')"
        page.click(download_button_selector)
        
        image_selector = "img.fullsize-image"
        if not wait_for_element(page, image_selector):
            logger.error("Could not find the full-size image element")
            return False
        
        image_src = page.get_attribute(image_selector, "src")
        if not image_src:
            logger.error("Could not get image source URL")
            return False
            
        image_page = page.context.new_page()
        image_page.goto(image_src)
        image_content = image_page.content()
        
        import re
        image_data_match = re.search(r'<img src="data:image/png;base64,([^"]+)"', image_content)
        if not image_data_match:
            logger.error("Could not extract image data")
            image_page.close()
            return False
            
        import base64
        image_data = image_data_match.group(1)
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_data))
            
        image_page.close()
        logger.info(f"Image successfully saved to {image_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return False

def log_session_result(logger: logging.Logger, prompt: str, status: str, 
                      file_path: Optional[str] = None, error: Optional[str] = None,
                      elapsed_time: Optional[float] = None) -> None:
    """
    Log the result of the image generation session.
    
    Args:
        logger: Logger instance
        prompt: The text prompt used
        status: SUCCESS or FAILURE
        file_path: Path to the saved image (for successful generations)
        error: Error message (for failed generations)
        elapsed_time: Time taken for the operation in seconds
    """
    logger.info("-" * 50)
    logger.info(f"Prompt used: \"{prompt}\"")
    logger.info(f"Status: {status}")
    
    if status == "SUCCESS" and file_path:
        logger.info(f"File: {file_path}")
        if elapsed_time:
            logger.info(f"Time: {elapsed_time:.1f}s")
    elif status == "FAILURE" and error:
        logger.error(f"Error: {error}")
        
    logger.info("-" * 50)
