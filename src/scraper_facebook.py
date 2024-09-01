import time
from typing import Optional, List, Any
import re
import json
import datetime
import pandas as pd

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

from src.scraper import BaseScraper
from src.types import Offer, User
from src.util.override import overrides

BUTTON_WAIT_TIMEOUT = 3
SCROLL_TIMEOUT = 2

DEBUG_MODE = True
FACEBOOK_RADII = [1, 2, 5, 10, 20, 40, 60, 65, 80, 1000, 250, 500]

FACEBOOK_BASE_URL = 'https://www.facebook.com'
URL = FACEBOOK_BASE_URL + '/marketplace/search?query={query}&exact=false'


@contextmanager
def ignore_error(success_message: Optional[str] = None, error_message: str = 'An error occurred {e}!'):
    try:
        yield
        if success_message is not None:
            print(success_message)
    except Exception as e:
        print(error_message.format(e))

        if DEBUG_MODE:
            raise e


def get_browser(headless=True) -> webdriver.Chrome:
    chrome_install = ChromeDriverManager().install()
    chromedriver_path = chrome_install
    chrome_options = Options()
    # Initialize Chrome WebDriver
    if headless:
        chrome_options.add_argument('--headless')
    # required to load interactive elements in headless mode
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
    return browser


def _find_key(key, obj) -> Optional[Any]:
    if isinstance(obj, dict):
        for k in obj:
            if k == key:
                return obj[k]
            res = _find_key(key, obj[k])
            if res is not None:
                return res
    elif isinstance(obj, list):
        for e in obj:
            res = _find_key(key, e)
            if res is not None:
                return res


def get_product_data(url: str, browser: webdriver.Chrome) -> Any:
    # use selenium to load complete html (including price)
    browser.get(url)
    time.sleep(2)
    soup = BeautifulSoup(browser.page_source, 'html.parser')

    scripts = soup.find_all('script')
    for script in scripts:
        json_texts = re.findall(r'{.*}', script.string)
        for json_text in json_texts:
            if 'price' in json_text:
                json_data = json.loads(json_text)
                return _find_key('target', json_data)

    raise ValueError('Could not find product data')


class ScraperFacebook(BaseScraper):
    def __init__(self, location: str, distance: float, max_pages_to_scrape: int = 1000):
        super().__init__(offer_page_batch_size=10, max_offers_per_page=25, max_pages_to_scrape=max_pages_to_scrape)
        self.browser = get_browser()
        self.location = location
        self.distance = distance

    @overrides(BaseScraper)
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        # Return only the relevant search URLs for the current scraper
        return [url for url in urls if FACEBOOK_BASE_URL in url]

    @overrides(BaseScraper)
    async def scrape_offer_url(self, url: str) -> Offer:
        data = get_product_data(url, self.browser)

        offer_id = data['id']
        offer_title = data['marketplace_listing_title']  # type: ignore
        offer_description = data['redacted_description']
        offer_price = data['listing_price']['amount']
        offer_location = data['location_text']
        timestamp = data['creation_time']
        offer_date = datetime.datetime.utcfromtimestamp(timestamp)
        offer_image_urls = []  # TODO [img['src'] for img in soup.find_all(id='viewad-image')]

        user_id = '# TODO'
        user_name = '# TODO'
        user_rating = '# TODO'
        user_all_offers_link = '# TODO'

        # Extract user details
        # userprofile_vip = soup.find(class_='userprofile-vip')
        # if userprofile_vip and userprofile_vip.a:  # type: ignore
        #     user_link = userprofile_vip.a['href']  # type: ignore
        #     user_id = user_link.split('=')[-1]  # type: ignore
        #     user_name = userprofile_vip.a.text.strip()  # type: ignore
        # else:
        #     user_link = 'No user link'
        #     user_id = 'No user id'
        #     user_name = 'No user name'

        # user_badge_tag = soup.find(class_='userbadge-tag')
        # if user_badge_tag:
        #     user_rating = user_badge_tag.text.strip()
        # else:
        #     user_rating = 'No rating'
        # user_all_offers_link = BASE_URL_KLEINANZEIGEN + user_link  # type: ignore

        user = User(
            id=user_id,
            name=user_name,
            rating=user_rating,
            all_offers_link=user_all_offers_link,
        )

        # Create data class instances
        offer = Offer(
            id=offer_id,
            title=offer_title,
            description=offer_description,
            price=offer_price,
            location=offer_location,
            date=str(offer_date),
            link=url,
            sold=False,
            image_urls=offer_image_urls,
            user=user,
            scraped_on=pd.Timestamp.now(),
        )

        return offer

    @overrides(BaseScraper)
    async def scrape_offer_links_from_search_url(self, base_url: str) -> List[str]:
        self.browser.get(base_url)

        with ignore_error('Decline button clicked!', 'Could not find or click the optional cookies button!'):
            decline_button_parent = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Decline optional cookies']/ancestor::div[contains(@role, 'button')]")
                )
            )
            decline_button_parent.click()

        with ignore_error('Close button clicked!', 'Could not find or click the close button!'):
            close_button = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Close" and @role="button"]'))
            )
            close_button.click()

        closest_distance = str(min(FACEBOOK_RADII, key=lambda x: abs(x - self.distance)))
        print(f'Facebook distance used: {closest_distance} kilometers')

        # location is critical
        button = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(., 'San Francisco')]"))
        )

        button.click()
        location_input = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Location']"))
        )

        location_input.send_keys(Keys.CONTROL + 'a')
        location_input.send_keys(Keys.DELETE)

        location_input.send_keys(self.location)

        location_option = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//span[contains(text(), '{self.location}')]/ancestor::div[@role='option']")
            )
        )
        localtion_option_text = location_option.text
        location_option.click()
        print(f'Location set to {localtion_option_text}')

        with ignore_error('Set distance!', 'Could not set distance!'):
            distance_element = WebDriverWait(self.browser, BUTTON_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//label[@aria-label='Radius']"))
            )
            distance_element.click()

            _ = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='listbox']"))
            )
            options = self.browser.find_elements(By.XPATH, "//div[@role='option']//span")
            for option in options:
                if closest_distance in option.text:
                    option.click()
                    break
            else:
                raise ValueError(f'Could not find the distance option for {closest_distance} kilometers!')

        apply_button = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and .//span[text()='Apply']]"))
        )

        apply_button.click()

        time.sleep(SCROLL_TIMEOUT)

        last_height = self.browser.execute_script('return document.body.scrollHeight')
        while True:
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(SCROLL_TIMEOUT)
            new_height = self.browser.execute_script('return document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height
            print('scrolled')

        html = self.browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        self.browser.close()

        links = [e.get('href') for e in soup.find_all('a')]
        item_urls = [FACEBOOK_BASE_URL + e for e in links if e and e.startswith('/marketplace/item/')]
        return item_urls


async def main():
    # Setup search parameters
    city = 'Karlsruhe'
    distance = 90
    product = 'Windsurfing board'

    scraper = ScraperFacebook(location=city, distance=distance)
    all_offers = await scraper.scrape_all_offers(
        [
            URL.format(query=product),
        ]
    )

    for offer in all_offers:
        print(offer)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
