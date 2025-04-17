"""
Stealth browser launcher for Sora image generator.
Provides a Playwright browser instance configured to bypass Cloudflare detection.
"""
import os
import json
import random
import logging
from typing import Dict, Any, Optional, List, Tuple

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},  # Full HD
    {"width": 1366, "height": 768},   # Common laptop
    {"width": 1440, "height": 900},   # MacBook
    {"width": 2560, "height": 1440},  # QHD
]

def get_random_user_agent() -> str:
    """Get a random user agent from the list."""
    return random.choice(USER_AGENTS)

def get_random_viewport() -> Dict[str, int]:
    """Get a random viewport size from the list."""
    return random.choice(VIEWPORT_SIZES)

def launch_stealth_browser(
    headless: bool = False,
    user_agent: Optional[str] = None,
    viewport: Optional[Dict[str, int]] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[Browser, BrowserContext]:
    """
    Launch a browser with stealth mode to bypass Cloudflare detection.
    
    Args:
        headless: Whether to run the browser in headless mode
        user_agent: Custom user agent string (random one used if None)
        viewport: Custom viewport size (random one used if None)
        logger: Logger instance for debug information
        
    Returns:
        Tuple of (Browser, BrowserContext) instances
    """
    if logger:
        logger.info("Launching stealth browser")
    
    if user_agent is None:
        user_agent = get_random_user_agent()
        if logger:
            logger.info(f"Using random user agent: {user_agent}")
    
    if viewport is None:
        viewport = get_random_viewport()
        if logger:
            logger.info(f"Using random viewport: {viewport}")
    
    playwright = sync_playwright().start()
    
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--start-maximized',
            '--hide-scrollbars',
            '--mute-audio',
            '--disable-infobars',
            '--disable-breakpad',
            '--disable-canvas-aa',
            '--disable-2d-canvas-clip-aa',
            '--disable-gl-drawing-for-tests',
            '--enable-webgl',
            '--use-gl=swiftshader',
            '--use-angle=swiftshader',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--allow-running-insecure-content',
            '--disable-notifications',
            '--disable-popup-blocking',
            '--disable-extensions',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-ipc-flooding-protection',
            '--disable-sync',
            '--metrics-recording-only',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
            '--disable-print-preview',
            '--disable-speech-api',
            '--disable-background-networking',
            '--disable-background-networking',
            '--disable-domain-reliability',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-sync',
            '--disable-default-apps',
            '--disable-translate',
            '--disable-extensions',
            '--disable-popup-blocking',
            '--disable-ipc-flooding-protection',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-background-timer-throttling',
            '--disable-background-networking',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-domain-reliability',
            '--disable-sync',
            '--disable-features=TranslateUI,BlinkGenPropertyTrees',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-sync',
            '--disable-translate',
            '--metrics-recording-only',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-pings',
            '--password-store=basic',
            '--use-mock-keychain',
            '--no-zygote',
            '--lang=en-US,en;q=0.9',
            '--new-window',
            '--incognito',
        ]
    )
    
    context = browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale="en-US",
        timezone_id="Europe/Paris",  # Set to France timezone
        geolocation={"latitude": 48.8566, "longitude": 2.3522},  # Paris coordinates
        permissions=["geolocation"],
        ignore_https_errors=True,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",  # Include French as secondary language
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-ch-ua": '"Chromium";v="123", "Google Chrome";v="123", "Not:A-Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
        }
    )
    
    if logger:
        logger.info("Stealth browser launched successfully")
    
    return browser, context

def setup_stealth_page(page: Page, logger: Optional[logging.Logger] = None) -> Page:
    """
    Apply additional stealth techniques to a page to bypass detection.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        
    Returns:
        The configured page
    """
    if logger:
        logger.info("Setting up stealth page")
    
    page.add_init_script("""
    function() {
        // Override the webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: function() { return undefined; }
        });
        
        // Override the plugins to include some
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                return [
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        name: "Chrome PDF Plugin",
                        filename: "internal-pdf-viewer",
                        description: "Portable Document Format",
                        length: 1
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        name: "Chrome PDF Viewer",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        description: "Portable Document Format",
                        length: 1
                    },
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        name: "Native Client",
                        filename: "internal-nacl-plugin",
                        description: "Native Client Executable",
                        length: 1
                    }
                ];
            }
        });
        
        // Override the languages property
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en', 'fr']; }
        });
        
        // Override the permissions API
        if (navigator.permissions) {
            navigator.permissions.__proto__.query = function(parameters) {
                return { state: 'granted', onchange: null };
            };
        }
        
        // Override the connection property
        Object.defineProperty(navigator, 'connection', {
            get: function() {
                return {
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                };
            }
        });
        
        // Override the hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: function() { return 8; }
        });
        
        // Override the device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: function() { return 8; }
        });
        
        // Override the platform
        Object.defineProperty(navigator, 'platform', {
            get: function() { return 'Win32'; }
        });
        
        // Override the userAgent
        Object.defineProperty(navigator, 'userAgent', {
            get: function() { return window.navigator.userAgent; }
        });
        
        // Override the Chrome property
        window.chrome = {
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: 'disabled',
                    INSTALLED: 'installed',
                    NOT_INSTALLED: 'not_installed'
                },
                RunningState: {
                    CANNOT_RUN: 'cannot_run',
                    READY_TO_RUN: 'ready_to_run',
                    RUNNING: 'running'
                }
            },
            runtime: {
                OnInstalledReason: {
                    CHROME_UPDATE: 'chrome_update',
                    INSTALL: 'install',
                    SHARED_MODULE_UPDATE: 'shared_module_update',
                    UPDATE: 'update'
                },
                OnRestartRequiredReason: {
                    APP_UPDATE: 'app_update',
                    OS_UPDATE: 'os_update',
                    PERIODIC: 'periodic'
                },
                PlatformArch: {
                    ARM: 'arm',
                    ARM64: 'arm64',
                    MIPS: 'mips',
                    MIPS64: 'mips64',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64'
                },
                PlatformNaclArch: {
                    ARM: 'arm',
                    MIPS: 'mips',
                    MIPS64: 'mips64',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64'
                },
                PlatformOs: {
                    ANDROID: 'android',
                    CROS: 'cros',
                    LINUX: 'linux',
                    MAC: 'mac',
                    OPENBSD: 'openbsd',
                    WIN: 'win'
                },
                RequestUpdateCheckStatus: {
                    NO_UPDATE: 'no_update',
                    THROTTLED: 'throttled',
                    UPDATE_AVAILABLE: 'update_available'
                }
            }
        };
        
        // Add missing function
        window.navigator.javaEnabled = function() { return false; };
        
        // Override the permissions API
        const originalQuery = window.navigator.permissions?.query;
        window.navigator.permissions.query = function(parameters) {
            if (parameters.name === 'notifications') {
                return { state: Notification.permission, onchange: null };
            } else {
                return originalQuery(parameters);
            }
        };
        
        // Pass the Cloudflare test
        window.navigator.permissions.query = function(parameters) {
            return {
                state: parameters.name === "notifications" ? "denied" : "granted",
                onchange: null
            };
        };
        
        // Prevent iframe detection
        try {
            Object.defineProperty(window.HTMLIFrameElement.prototype, 'contentWindow', {
                get: function() {
                    return window;
                }
            });
        } catch (e) {}
        
        // Spoof screen resolution
        Object.defineProperty(window.screen, 'availWidth', { get: function() { return 1920; } });
        Object.defineProperty(window.screen, 'availHeight', { get: function() { return 1080; } });
        Object.defineProperty(window.screen, 'width', { get: function() { return 1920; } });
        Object.defineProperty(window.screen, 'height', { get: function() { return 1080; } });
        Object.defineProperty(window.screen, 'colorDepth', { get: function() { return 24; } });
        Object.defineProperty(window.screen, 'pixelDepth', { get: function() { return 24; } });
        
        // Add touch support
        const touchSupport = {
            maxTouchPoints: 5,
            touchEvent: function() { return true; },
            touchStart: function() { return true; }
        };
        Object.defineProperty(navigator, 'maxTouchPoints', { get: function() { return touchSupport.maxTouchPoints; } });
        
        // Add missing functions
        if (window.navigator.languages === undefined) {
            Object.defineProperty(navigator, 'languages', { get: function() { return ['en-US', 'en']; } });
        }
        
        // Override toString methods to avoid detection
        const nativeToStringFunctionString = Error.toString().replace(/Error/g, "toString");
        const nativeCodeString = "function code() { [native code] }";
        const nativeFunctionString = "function () { [native code] }";
        
        // Override toString of Function
        Function.prototype.toString = function() {
            if (this === Function.prototype.toString) {
                return nativeToStringFunctionString;
            }
            if (this === Function.prototype.valueOf) {
                return nativeFunctionString;
            }
            return nativeFunctionString;
        };
    }
    """)
    
    page.evaluate("""
    function() {
        // Add random mouse movements
        const randomMouseMovement = function() {
            const event = new MouseEvent('mousemove', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': Math.floor(Math.random() * window.innerWidth),
                'clientY': Math.floor(Math.random() * window.innerHeight)
            });
            document.dispatchEvent(event);
        };
        
        // Simulate random mouse movements
        setInterval(randomMouseMovement, Math.floor(Math.random() * 2000) + 1000);
        
        // Simulate random scrolling
        const randomScroll = function() {
            window.scrollBy({
                top: Math.floor(Math.random() * 100) - 50,
                behavior: 'smooth'
            });
        };
        
        // Simulate random scrolling
        setInterval(randomScroll, Math.floor(Math.random() * 5000) + 3000);
    }
    """)
    
    if logger:
        logger.info("Stealth page setup complete")
    
    return page

def apply_session_state(context: BrowserContext, session_file: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Apply session state from a session.json file to the browser context.
    
    Args:
        context: Playwright browser context
        session_file: Path to the session.json file
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(session_file):
        if logger:
            logger.error(f"Session file not found: {session_file}")
        return False
    
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        
        if logger:
            logger.info(f"Processing session data from {session_file}")
        
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
        
        if logger:
            logger.info(f"Adding {len(processed_cookies)} processed cookies to browser context")
        
        context.add_cookies(processed_cookies)
        
        if "origins" in session_data and session_data["origins"]:
            if logger:
                logger.info("Setting storage state from session.json")
            
            for origin in session_data.get("origins", []):
                origin_url = origin.get("origin")
                if origin_url and "sora" in origin_url:
                    if logger:
                        logger.info(f"Setting storage for origin: {origin_url}")
                    
                    if "localStorage" in origin:
                        page = context.new_page()
                        page.goto(origin_url)
                        for item in origin.get("localStorage", []):
                            page.evaluate("""function(key, value) {
                                localStorage.setItem(key, value);
                                return true;
                            }""", item.get("name"), item.get("value"))
                        page.close()
                        
                    if "sessionStorage" in origin:
                        page = context.new_page()
                        page.goto(origin_url)
                        for item in origin.get("sessionStorage", []):
                            page.evaluate("""function(key, value) {
                                sessionStorage.setItem(key, value);
                                return true;
                            }""", item.get("name"), item.get("value"))
                        page.close()
        
        if logger:
            logger.info("Session state applied successfully")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Error applying session state: {str(e)}")
        return False

def handle_cloudflare_challenge(page: Page, logger: Optional[logging.Logger] = None) -> bool:
    """
    Handle Cloudflare challenge pages by simulating human behavior.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        
    Returns:
        True if successfully bypassed, False otherwise
    """
    if logger:
        logger.info("Checking for Cloudflare challenge")
    
    is_cloudflare = page.evaluate("""function() {
        return document.title.includes("Cloudflare") || 
               document.title.includes("Just a moment") ||
               document.body.innerText.includes("Cloudflare") ||
               document.body.innerText.includes("checking your browser") ||
               document.body.innerText.includes("Please wait") ||
               document.body.innerText.includes("Please turn JavaScript on");
    }""")
    
    if not is_cloudflare:
        if logger:
            logger.info("No Cloudflare challenge detected")
        return True
    
    if logger:
        logger.info("Cloudflare challenge detected, attempting to bypass")
    
    page.wait_for_timeout(5000)
    
    page.mouse.move(
        x=random.randint(100, 700),
        y=random.randint(100, 500)
    )
    
    for _ in range(5):
        page.mouse.move(
            x=random.randint(100, 700),
            y=random.randint(100, 500)
        )
        page.wait_for_timeout(random.randint(500, 1500))
    
    page.mouse.wheel(delta_y=300)
    page.wait_for_timeout(1000)
    page.mouse.wheel(delta_y=-150)
    
    page.wait_for_timeout(10000)
    
    still_cloudflare = page.evaluate("""function() {
        return document.title.includes("Cloudflare") || 
               document.title.includes("Just a moment") ||
               document.body.innerText.includes("Cloudflare") ||
               document.body.innerText.includes("checking your browser");
    }""")
    
    if still_cloudflare:
        if logger:
            logger.warning("Still on Cloudflare challenge page after initial attempt")
        
        try:
            page.click("body", position={"x": 100, "y": 100})
            page.wait_for_timeout(2000)
        except:
            pass
        
        page.wait_for_timeout(15000)
        
        final_check = page.evaluate("""function() {
            return document.title.includes("Cloudflare") || 
                   document.title.includes("Just a moment") ||
                   document.body.innerText.includes("Cloudflare") ||
                   document.body.innerText.includes("checking your browser");
        }""")
        
        if final_check:
            if logger:
                logger.error("Failed to bypass Cloudflare challenge")
            return False
    
    if logger:
        logger.info("Successfully bypassed Cloudflare challenge")
    
    return True

def verify_sora_access(page: Page, logger: Optional[logging.Logger] = None) -> bool:
    """
    Verify that we have successfully accessed the Sora website.
    
    Args:
        page: Playwright page object
        logger: Logger instance
        
    Returns:
        True if access is verified, False otherwise
    """
    if logger:
        logger.info("Verifying Sora access")
    
    region_restricted = page.evaluate("""function() {
        return document.body.innerText.includes("not available in your country") ||
               document.body.innerText.includes("not available in your region");
    }""")
    
    if region_restricted:
        if logger:
            logger.error("Sora is not available in the current region/country")
        return False
    
    has_interface = page.evaluate("""function() {
        // Look for common Sora interface elements
        const hasTextarea = !!document.querySelector('textarea');
        const hasInputField = !!document.querySelector('input[type="text"]');
        const hasContentEditable = !!document.querySelector('[contenteditable="true"]');
        
        // Look for Sora-specific elements or text
        const hasSoraText = document.body.innerText.includes("Sora") ||
                           document.body.innerText.includes("Generate") ||
                           document.body.innerText.includes("Create");
        
        return (hasTextarea || hasInputField || hasContentEditable) && hasSoraText;
    }""")
    
    if not has_interface:
        if logger:
            logger.warning("Could not verify Sora interface elements")
        
        try:
            page.screenshot(path="sora_access_check.png")
            if logger:
                logger.info("Saved screenshot to sora_access_check.png")
        except:
            pass
        
        try:
            html_content = page.content()
            with open("sora_access_check.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            if logger:
                logger.info("Saved HTML to sora_access_check.html")
        except:
            pass
        
        return False
    
    if logger:
        logger.info("Successfully verified Sora access")
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger("stealth_launcher")
    
    browser, context = launch_stealth_browser(headless=False, logger=logger)
    page = context.new_page()
    page = setup_stealth_page(page, logger)
    
    logger.info("Navigating to Sora website")
    page.goto("https://sora.com")
    
    if handle_cloudflare_challenge(page, logger):
        logger.info("Cloudflare challenge handled successfully")
    else:
        logger.error("Failed to handle Cloudflare challenge")
    
    if verify_sora_access(page, logger):
        logger.info("Successfully accessed Sora website")
    else:
        logger.error("Failed to access Sora website")
    
    page.screenshot(path="sora_test.png")
    logger.info("Screenshot saved to sora_test.png")
    
    input("Press Enter to close the browser...")
    
    browser.close()
