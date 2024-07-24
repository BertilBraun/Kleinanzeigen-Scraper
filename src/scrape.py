import asyncio
import requests
from bs4 import BeautifulSoup

from src.config import BASE_URL, MAX_OFFERS_PER_PAGE
from src.requests import get
from src.types import Offer, User
from src.util import log_all_exceptions


async def scrape_offer_url(url: str) -> Offer:
    html_content = await get(url)
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract offer details
    offer_id = soup.find(id='viewad-ad-id-box').find_all('li')[1].text.strip()
    offer_title = soup.find(id='viewad-title').text.strip()
    offer_description = soup.find(id='viewad-description-text').text.strip()
    offer_price = soup.find(id='viewad-price').text.strip()
    offer_location = soup.find(id='viewad-locality').text.strip()
    offer_date = soup.find(id='viewad-extra-info').div.span.text.strip()
    offer_image_urls = [img['src'] for img in soup.find_all(id='viewad-image')]

    # Extract user details
    user_link = soup.find(class_='userprofile-vip').a['href']
    user_id = user_link.split('=')[-1]
    user_name = soup.find(class_='userprofile-vip').a.text.strip()
    user_badge_tag = soup.find(class_='userbadge-tag')
    if user_badge_tag:
        user_rating = user_badge_tag.text.strip()
    else:
        user_rating = 'No rating'
    user_all_offers_link = BASE_URL + user_link

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
    )

    return offer


def scrape_offer_links_from_search_url(base_url: str) -> list[str]:
    # Send a GET request to the specified URL
    response = requests.get(base_url)
    response.raise_for_status()  # Raises an HTTPError for bad responses (4XX, 5XX)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all <a> tags and filter by href attribute
    links: list[str] = []
    for a in soup.find_all('article'):
        href = a['data-href']
        # Check if 's-anzeige' is in the URL and if the URL starts with the expected path
        if 's-anzeige' in href and href.startswith('/s-anzeige/'):
            links.append(BASE_URL + href)

    return links


def scrape_all_offer_links_from_search_url(search_url: str) -> list[str]:
    all_offer_links: set[str] = set()

    for page in range(1, 50):
        print(f'Scraping page {page}...')
        try:
            offer_links = scrape_offer_links_from_search_url(search_url.format(page))
        except Exception as e:
            print(f'Error while scraping page {page}: {e}')
            break
        print(f'Found {len(offer_links)} offers on page {page}.')

        all_offer_links.update(offer_links)

        if len(offer_links) < MAX_OFFERS_PER_PAGE:
            # TODO this breaks if there are exactly 25 offers on the last page. At least no link should be added twice since it's a set.
            break

    return list(all_offer_links)


async def scrape_all_offers(all_offer_links: list[str]) -> list[Offer]:
    offer_futures = [scrape_offer_url(url) for url in all_offer_links]
    offers: list[Offer] = []
    for offer in asyncio.as_completed(offer_futures):
        with log_all_exceptions('while scraping offer'):
            offers.append(await offer)
    return offers
