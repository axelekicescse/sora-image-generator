"""
Utility functions for Sora image generation.
Contains helper functions for browser interactions, DOM manipulation, and error handling.
"""
import os
import re
import time
import base64
import hashlib
import logging
import unittest
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Callable

DEFAULT_CONFIG = {
    "SORA_URL": "https://sora.com",
    "HEADLESS": "False",
    "LOG_LEVEL": "INFO",
    "MAX_RETRIES": "3",
    "RETRY_DELAY": "2",
    "WAIT_TIMEOUT": "60",
    "GENERATION_TIMEOUT": "300",
    "IMAGE_DIR": "images",
    "LOG_DIR": "logs"
}

def load_env_config() -> Dict[str, str]:
    """
    Load configuration from .env file if it exists, otherwise use defaults.
    
    Returns:
        Dictionary with configuration values
    """
    config = DEFAULT_CONFIG.copy()
    
    try:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        for key in config:
            env_value = os.environ.get(key)
            if env_value is not None:
                config[key] = env_value
                
    except Exception as e:
        print(f"Warning: Error loading .env configuration: {str(e)}")
        
    return config

CONFIG = load_env_config()

def setup_logging(log_dir: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Logger instance
    """
    if log_dir is None:
        log_dir = CONFIG["LOG_DIR"]
        
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{timestamp}_sora.log")
    
    logger = logging.getLogger("sora_image_generator")
    
    log_level = getattr(logging, CONFIG["LOG_LEVEL"].upper(), logging.INFO)
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def generate_image_filename(prompt: str, image_dir: Optional[str] = None) -> str:
    """
    Generate a unique filename for the image based on timestamp and prompt hash.
    
    Args:
        prompt: The text prompt used to generate the image
        image_dir: Directory to store images
        
    Returns:
        Full path to the image file
    """
    if image_dir is None:
        image_dir = CONFIG["IMAGE_DIR"]
        
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:6]
    
    filename = f"{timestamp}_{prompt_hash}.png"
    
    return os.path.join(image_dir, filename)

def with_retry(max_retries: Optional[int] = None, retry_delay: Optional[int] = None) -> Callable:
    """
    Decorator to add retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    if max_retries is None:
        max_retries = int(CONFIG["MAX_RETRIES"])
        
    if retry_delay is None:
        retry_delay = int(CONFIG["RETRY_DELAY"])
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = None
            for arg in args:
                if isinstance(arg, logging.Logger):
                    logger = arg
                    break
                    
            if logger is None and 'logger' in kwargs:
                logger = kwargs['logger']
                
            attempts = 0
            last_error = None
            
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_error = e
                    
                    if logger:
                        logger.warning(f"Attempt {attempts}/{max_retries} failed for {func.__name__}: {str(e)}")
                    
                    if attempts < max_retries:
                        if logger:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        
            if logger:
                logger.error(f"All {max_retries} attempts failed for {func.__name__}")
                
            if last_error:
                raise last_error
                
            return False
            
        return wrapper
    return decorator

@with_retry()
def wait_for_element(page, selector: str, logger: Optional[logging.Logger] = None, 
                    timeout: Optional[int] = None, state: str = "visible") -> bool:
    """
    Wait for an element to appear on the page with retry mechanism.
    
    Args:
        page: Playwright page object
        selector: CSS or XPath selector
        logger: Logger instance
        timeout: Maximum time to wait in seconds
        state: Element state to wait for (visible, hidden, attached, detached)
        
    Returns:
        True if element was found, False if timeout occurred
    """
    if timeout is None:
        timeout = int(CONFIG["WAIT_TIMEOUT"])
        
    if logger:
        logger.debug(f"Waiting for element: {selector} (state={state}, timeout={timeout}s)")
        
    try:
        page.wait_for_selector(selector, state=state, timeout=timeout * 1000)
        if logger:
            logger.debug(f"Element found: {selector}")
        return True
    except Exception as e:
        if logger:
            logger.warning(f"Element not found: {selector} - {str(e)}")
        raise  # Re-raise for retry mechanism

def check_for_errors(page, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """
    Check for common error messages on the page.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        
    Returns:
        Tuple of (error_found, error_message)
    """
    error_selectors = [
        "text='An error occurred'",
        "text='Something went wrong'",
        "text='Please try again'",
        "text='Error'",
        ".error-message",
        "[data-testid='error']"
    ]
    
    for selector in error_selectors:
        try:
            if page.is_visible(selector):
                try:
                    error_text = page.text_content(selector)
                    logger.error(f"Error detected on page: {error_text}")
                    return True, error_text
                except:
                    logger.error(f"Error element detected: {selector}")
                    return True, f"Error element detected: {selector}"
        except Exception:
            pass
            
    return False, None

def wait_for_image_generation(page, logger: logging.Logger, timeout: Optional[int] = None) -> bool:
    """
    Wait for image generation to complete by checking for the download button.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if image generation completed, False if timeout occurred
    """
    if timeout is None:
        timeout = int(CONFIG["GENERATION_TIMEOUT"])
        
    logger.info("Waiting for image generation to complete...")
    start_time = time.time()
    
    download_button_selector = "button:has-text('Download')"
    
    time.sleep(2)  # Short delay to allow initial errors to appear
    has_error, error_message = check_for_errors(page, logger)
    if has_error:
        logger.error(f"Error detected early in generation process: {error_message}")
        return False
    
    while time.time() - start_time < timeout:
        try:
            if page.is_visible(download_button_selector):
                elapsed_time = time.time() - start_time
                logger.info(f"Image generation completed in {elapsed_time:.1f} seconds")
                return True
            
            has_error, error_message = check_for_errors(page, logger)
            if has_error:
                return False
                
            progress_selector = ".progress-indicator"
            try:
                if page.is_visible(progress_selector):
                    progress_text = page.text_content(progress_selector)
                    logger.debug(f"Generation progress: {progress_text}")
            except:
                pass
                
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Exception while checking image status: {str(e)}")
            time.sleep(2)
    
    logger.error(f"Timeout after {timeout} seconds waiting for image generation")
    return False

@with_retry()
def download_image(page, image_path: str, logger: logging.Logger) -> bool:
    """
    Download the generated image with retry mechanism.
    
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
        if not wait_for_element(page, image_selector, logger):
            logger.error("Could not find the full-size image element")
            raise Exception("Could not find the full-size image element")
        
        image_src = page.get_attribute(image_selector, "src")
        if not image_src:
            logger.error("Could not get image source URL")
            raise Exception("Could not get image source URL")
            
        image_page = page.context.new_page()
        image_page.goto(image_src)
        image_content = image_page.content()
        
        image_data_match = re.search(r'<img src="data:image/png;base64,([^"]+)"', image_content)
        if not image_data_match:
            logger.error("Could not extract image data")
            image_page.close()
            raise Exception("Could not extract image data")
            
        image_data = image_data_match.group(1)
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_data))
            
        image_page.close()
        logger.info(f"Image successfully saved to {image_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        raise  # Re-raise for retry mechanism

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

class TestSoraUtils(unittest.TestCase):
    """Unit tests for Sora utility functions."""
    
    def test_generate_image_filename(self):
        """Test the generate_image_filename function."""
        prompt = "Test prompt"
        test_dir = "test_images"
        
        filename = generate_image_filename(prompt, test_dir)
        
        self.assertTrue(os.path.exists(test_dir))
        self.assertTrue(filename.startswith(test_dir + "/"))
        self.assertTrue(filename.endswith(".png"))
        
        basename = os.path.basename(filename)
        parts = basename.split("_")
        
        self.assertEqual(len(parts), 3)
        
        date_part = parts[0]
        self.assertEqual(len(date_part), 8)
        self.assertTrue(date_part.isdigit())
        
        time_part = parts[1]
        self.assertEqual(len(time_part), 6)
        self.assertTrue(time_part.isdigit())
        
        hash_part = parts[2]
        self.assertEqual(len(hash_part), 10)  # 6 for hash + 4 for .png
        self.assertTrue(hash_part.endswith(".png"))
        
        try:
            os.rmdir(test_dir)
        except:
            pass
    
    def test_log_session_result(self):
        """Test the log_session_result function."""
        import io
        log_stream = io.StringIO()
        
        test_logger = logging.getLogger("test_logger")
        test_logger.setLevel(logging.INFO)
        
        if test_logger.handlers:
            test_logger.handlers.clear()
            
        handler = logging.StreamHandler(log_stream)
        formatter = logging.Formatter('[%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
        
        log_session_result(
            test_logger,
            prompt="Test prompt",
            status="SUCCESS",
            file_path="/path/to/image.png",
            elapsed_time=42.5
        )
        
        log_output = log_stream.getvalue()
        
        self.assertIn("Prompt used: \"Test prompt\"", log_output)
        self.assertIn("Status: SUCCESS", log_output)
        self.assertIn("File: /path/to/image.png", log_output)
        self.assertIn("Time: 42.5s", log_output)
        
        log_stream.truncate(0)
        log_stream.seek(0)
        
        log_session_result(
            test_logger,
            prompt="Test prompt",
            status="FAILURE",
            error="Something went wrong"
        )
        
        log_output = log_stream.getvalue()
        
        self.assertIn("Prompt used: \"Test prompt\"", log_output)
        self.assertIn("Status: FAILURE", log_output)
        self.assertIn("Error: Something went wrong", log_output)

if __name__ == "__main__":
    unittest.main()
