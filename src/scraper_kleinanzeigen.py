from bs4 import BeautifulSoup
import pandas as pd

from src.config import BASE_URL_KLEINANZEIGEN
from src.util import get, overrides
from src.scraper import BaseScraper
from src.types import Offer, User


class ScraperKleinanzeigen(BaseScraper):
    def __init__(self, max_pages_to_scrape: int = 1000):
        super().__init__(offer_page_batch_size=10, max_offers_per_page=25, max_pages_to_scrape=max_pages_to_scrape)

    @overrides(BaseScraper)
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        return [url for url in urls if url.startswith(BASE_URL_KLEINANZEIGEN)]

    @overrides(BaseScraper)
    async def scrape_offer_url(self, url: str) -> Offer:
        html_content = await get(url)
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract offer details
        offer_id = soup.find(id='viewad-ad-id-box').find_all('li')[1].text.strip()  # type: ignore
        offer_title = soup.find(id='viewad-title').text.strip()  # type: ignore
        offer_description = soup.find(id='viewad-description-text').text.strip()  # type: ignore
        viewad_price = soup.find(id='viewad-price')
        if viewad_price:
            offer_price = viewad_price.text.strip()
        else:
            offer_price = 'No price'
        offer_location = soup.find(id='viewad-locality').text.strip()  # type: ignore
        offer_date = soup.find(id='viewad-extra-info').div.span.text.strip()  # type: ignore
        offer_image_urls = [img['src'] for img in soup.find_all(id='viewad-image')]

        # Extract user details
        userprofile_vip = soup.find(class_='userprofile-vip')
        if userprofile_vip and userprofile_vip.a:  # type: ignore
            user_link = userprofile_vip.a['href']  # type: ignore
            user_id = user_link.split('=')[-1]  # type: ignore
            user_name = userprofile_vip.a.text.strip()  # type: ignore
        else:
            user_link = 'No user link'
            user_id = 'No user id'
            user_name = 'No user name'

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

    @overrides(BaseScraper)
    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str | None]:
        from src.config_interests import TITLE_NO_GO_KEYWORDS

        # Send a GET request to the specified URL
        html_content = await get(base_url)

        # Parse the HTML content of the page
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all <a> tags and filter by href attribute
        links: list[str | None] = []
        for a in soup.find_all('article'):
            href = a['data-href']
            # Check if 's-anzeige' is in the URL and if the URL starts with the expected path
            if 's-anzeige' in href and href.startswith('/s-anzeige/'):
                # check if the title contains any of the no-go keywords
                if any(keyword in href.lower() for keyword in TITLE_NO_GO_KEYWORDS):
                    links.append(None)
                else:
                    links.append(BASE_URL_KLEINANZEIGEN + href)

        return links
