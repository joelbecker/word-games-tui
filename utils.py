import re
import curses
import os
import platform
from selenium import webdriver

WIDTH = 50


def is_termux():
    """Detect if running in Termux/Android environment"""
    # Check for Termux-specific environment variables
    if os.environ.get('TERMUX_VERSION') or os.environ.get('PREFIX', '').startswith('/data/data/com.termux'):
        return True
    
    # Check if we're in the Termux file system structure
    if os.path.exists('/data/data/com.termux/files/usr'):
        return True
    
    # Additional check for Android system
    try:
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            if 'android' in version_info:
                return True
    except (FileNotFoundError, PermissionError):
        pass
    
    return False


def scrape_with_selenium(url, driver_actions=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    if is_termux():
        # Termux/Android specific configuration
        chrome_options.add_experimental_option('androidPackage', 'com.android.chrome')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Use the chromedriver in current directory with Service
        service = Service('./chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        # Desktop configuration
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        
        # Let selenium find chromedriver in PATH
        driver = webdriver.Chrome(options=chrome_options)
        
    driver.get(url)
    if driver_actions:
        driver_actions(driver)
    html = driver.page_source
    driver.quit()
    return html


def strip_ansi(s):
    return re.sub(r'\x1b[^m]*m', '', s)
     

def justify(s, block=15, width=WIDTH, justify='left'):
    _justify = {
        'left': str.ljust,
        'right': str.rjust,
        'center': str.center
    }[justify]
    reference = strip_ansi(s)
    justified = _justify(reference, block or 0, ' ')
    centered = justified.center(width, ' ')
    result = centered.replace(reference, s)
    return result

def center_text(stdscr, text):
    return justify(text, justify='center', width=display_cols(stdscr))

def display_rows(stdscr):
    return min(stdscr.getmaxyx()[0], 24)
    

def display_cols(stdscr):
    return min(stdscr.getmaxyx()[1], 60)


def vertical_buffer(content_rows, display_rows):
    return (display_rows - content_rows) // 2


def horizontal_buffer(content_cols, display_cols):
    return (display_cols - content_cols) // 2


class Palette:

    @staticmethod
    def from_name(name):
        return getattr(Palette, name)()

    @staticmethod
    def purple():
        return curses.color_pair(170)

    @staticmethod
    def yellow():
        return curses.color_pair(227)

    @staticmethod
    def green():
        return curses.color_pair(43)

    @staticmethod
    def blue():
        return curses.color_pair(26)

    @staticmethod
    def red():
        return curses.color_pair(203)

    @staticmethod
    def white():
        return curses.color_pair(253)

    @staticmethod
    def gray():
        return curses.color_pair(240)


def full_page_screenshot(driver: webdriver.Chrome, path: str = '/tmp/screenshot.png') -> None:
    # Ref: https://stackoverflow.com/a/52572919/
    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    # driver.save_screenshot(path)  # has scrollbar
    driver.save_screenshot(path)  # avoids scrollbar
    driver.set_window_size(original_size['width'], original_size['height'])
