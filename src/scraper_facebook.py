import time
from typing import Optional
from src.util import get, overrides

from bs4 import BeautifulSoup
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from src.types import Offer

BUTTON_WAIT_TIMEOUT = 3
SCROLL_TIMEOUT = 2

DEBUG_MODE = True
FACEBOOK_RADII = [1, 2, 5, 10, 20, 40, 60, 65, 80, 1000, 250, 500]

#Setup search parameters
city = "Karlsruhe"
product = "Windsurfing board"
distance = 90

URL = 'https://www.facebook.com/marketplace/search?query={query}&exact=false'
FACEBOOK_BASE_URL = 'https://www.facebook.com'

@contextmanager
def ignore_error(
        success_message: Optional[str] = None,
        error_message: str = "An error occurred {e}!"
):
    try:
        yield
        if success_message is not None:
            print(success_message)
    except Exception as e:
        print(error_message.format(e))

        if DEBUG_MODE:
            raise e

def get_item_urls(location, query):
    url = URL.format(query=query)
    chrome_install = ChromeDriverManager().install()
    chromedriver_path = chrome_install
    chrome_options = Options()
    # Initialize Chrome WebDriver
    chrome_options.add_argument("--headless")
    # required to load interactive elements in headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(
        service = Service(chromedriver_path),
        options = chrome_options
    )
    browser.get(url)

    with ignore_error("Decline button clicked!", "Could not find or click the optional cookies button!"):
        decline_button_parent = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Decline optional cookies']/ancestor::div[contains(@role, 'button')]"))
        )
        decline_button_parent.click()

    with ignore_error("Close button clicked!", "Could not find or click the close button!"):
        close_button = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Close" and @role="button"]'))
        )
        close_button.click()

    closest_distance = str(min(FACEBOOK_RADII, key=lambda x: abs(x - distance)))
    print(f"Facebook distance used: {closest_distance} kilometers")

    # location is critical
    button = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(., 'San Francisco')]"))
    )

    button.click()
    location_input = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Location']"))
    )

    location_input.send_keys(Keys.CONTROL + "a")
    location_input.send_keys(Keys.DELETE)

    location_input.send_keys(location)

    location_option = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{location}')]/ancestor::div[@role='option']"))
    )
    localtion_option_text = location_option.text
    location_option.click()
    print(f"Location set to {localtion_option_text}")

    with ignore_error("Set distance!", "Could not set distance!"):
        distance_element = WebDriverWait(browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Radius']"))
        )
        distance_element.click()

        _ = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='listbox']"))
        )
        options = browser.find_elements(By.XPATH, "//div[@role='option']//span")
        for option in options:
            if closest_distance in option.text:
                option.click()
                break
        else:
            raise ValueError(f"Could not find the distance option for {closest_distance} kilometers!")

    apply_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and .//span[text()='Apply']]"))
    )

    apply_button.click()

    time.sleep(SCROLL_TIMEOUT)

    last_height = browser.execute_script("return document.body.scrollHeight")
    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_TIMEOUT)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        print("scrolled")

    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    browser.close()

    links = [e.get('href') for e in soup.find_all('a')]
    item_urls = [FACEBOOK_BASE_URL + e for e in links if e and e.startswith('/marketplace/item/')]
    return item_urls

