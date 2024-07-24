import asyncio
from bs4 import BeautifulSoup

from src.config import BASE_URL, MAX_OFFERS_PER_PAGE, OFFER_PAGE_BATCH_SIZE
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


async def scrape_offer_links_from_search_url(base_url: str) -> list[str]:
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
            links.append(BASE_URL + href)

    return links


async def scrape_all_offer_links_from_search_url(search_url: str) -> list[str]:
    all_offer_links: set[str] = set()

    for batch_start in range(1, 100, OFFER_PAGE_BATCH_SIZE):
        batch_end = batch_start + OFFER_PAGE_BATCH_SIZE
        offer_link_futures = [
            scrape_offer_links_from_search_url(search_url.format(page)) for page in range(batch_start, batch_end)
        ]
        for offer_links in asyncio.as_completed(offer_link_futures):
            with log_all_exceptions('while scraping offer links'):
                all_offer_links.update(await offer_links)

        if len(all_offer_links) < MAX_OFFERS_PER_PAGE * (batch_end - 1):
            break

    return list(all_offer_links)


async def scrape_all_offers(all_offer_links: list[str]) -> list[Offer]:
    offer_futures = [scrape_offer_url(url) for url in all_offer_links]
    offers: list[Offer] = []
    for offer in asyncio.as_completed(offer_futures):
        with log_all_exceptions('while scraping offer'):
            offers.append(await offer)
    return offers
