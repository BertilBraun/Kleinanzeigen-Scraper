from bs4 import BeautifulSoup
import pandas as pd

from src.config import BASE_URL_KLEINANZEIGEN
from src.requests import get
from src.scraper import BaseScraper
from src.types import Offer, User


class ScraperKleinanzeigen(BaseScraper):
    def __init__(self):
        super().__init__(offer_page_batch_size=10, max_offers_per_page=25)

    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        return [url for url in urls if 's-anzeige' in url and url.startswith(BASE_URL_KLEINANZEIGEN)]

    async def scrape_offer_url(self, url: str) -> Offer:
        html_content = await get(url)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract offer details
        offer_id = soup.find(id='viewad-ad-id-box').find_all('li')[1].text.strip()  # type: ignore
        offer_title = soup.find(id='viewad-title').text.strip()  # type: ignore
        offer_description = soup.find(id='viewad-description-text').text.strip()  # type: ignore
        offer_price = soup.find(id='viewad-price').text.strip()  # type: ignore
        offer_location = soup.find(id='viewad-locality').text.strip()  # type: ignore
        offer_date = soup.find(id='viewad-extra-info').div.span.text.strip()  # type: ignore
        offer_image_urls = [img['src'] for img in soup.find_all(id='viewad-image')]

        # Extract user details
        user_link = soup.find(class_='userprofile-vip').a['href']  # type: ignore
        user_id = user_link.split('=')[-1]  # type: ignore
        user_name = soup.find(class_='userprofile-vip').a.text.strip()  # type: ignore
        user_badge_tag = soup.find(class_='userbadge-tag')
        if user_badge_tag:
            user_rating = user_badge_tag.text.strip()
        else:
            user_rating = 'No rating'
        user_all_offers_link = BASE_URL_KLEINANZEIGEN + user_link  # type: ignore

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
        for a in soup.find_all('article'):
            href = a['data-href']
            # Check if 's-anzeige' is in the URL and if the URL starts with the expected path
            if 's-anzeige' in href and href.startswith('/s-anzeige/'):
                links.append(BASE_URL_KLEINANZEIGEN + href)

        return links
