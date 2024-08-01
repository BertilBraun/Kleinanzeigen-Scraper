from bs4 import BeautifulSoup
import pandas as pd

from src.config import BASE_URL_DAILYDOSE
from src.requests import get
from src.scraper import BaseScraper
from src.types import Offer, User


class ScraperDailyDose(BaseScraper):
    def __init__(self, max_pages_to_scrape: int = 1000):
        super().__init__(offer_page_batch_size=10, max_offers_per_page=30, max_pages_to_scrape=max_pages_to_scrape)

    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        return [url for url in urls if url.startswith(BASE_URL_DAILYDOSE)]

    async def scrape_offer_url(self, url: str) -> Offer:
        html_content = await get(url)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Navigate to the main 'foto_box' div to extract most details
        foto_box = soup.find('div', class_='fotos_box')

        # Extract title which is the first h1 within the foto_box
        offer_title = foto_box.find('h1').text.strip()  # type: ignore

        # Extract description which is the first p in the foto_box
        offer_description = ' '.join(foto_box.find('p').stripped_strings).replace('<br/>', '\n').strip()  # type: ignore

        # Extract details from the 'Anzeigendetails' section
        details = soup.find_all('span', style='color:rgba(255,255,255,0.4)')
        offer_price = details[0].next_sibling.strip() if details else 'None'
        offer_location = details[1].next_sibling.strip() if len(details) > 1 else 'None'
        user_name = details[2].next_sibling.strip() if len(details) > 2 else 'None'
        offer_date = details[3].next_sibling.strip() if len(details) > 3 else 'None'
        offer_id = details[4].next_sibling.strip() if len(details) > 4 else 'None'

        # Extract images based on the offer ID
        offer_image_urls = [
            BASE_URL_DAILYDOSE + '/' + img['src'] for img in soup.find_all('img', src=True) if offer_id in img['src']
        ]

        # Extract user ID from the href attribute for all user offers
        user_all_offers_link = BASE_URL_DAILYDOSE + '/' + soup.find('a', text='alle Anzeigen des Verkäufers')['href']  # type: ignore
        user_id = user_all_offers_link.split('/')[-1]  # Assuming the user ID is the last segment of the URL

        user = User(
            id=user_id,
            name=user_name,
            rating='DailyDose',
            all_offers_link=user_all_offers_link,
        )

        # Create data class instances
        offer = Offer(
            id=offer_id,
            title=offer_title,
            description=offer_description,
            price=offer_price,
            location=offer_location,
            date=offer_date,
            link=url,
            sold=False,
            image_urls=offer_image_urls,
            user=user,
            scraped_on=pd.Timestamp.now(),
        )

        return offer

    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str]:
        # Send a GET request to the specified URL
        html_content = await get(base_url)

        # Parse the HTML content of the page
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all <a> tags and filter by href attribute
        links: list[str] = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'detail.htm' in href and 'ai=' in href:
                links.append(BASE_URL_DAILYDOSE + '/' + href)

        return links
