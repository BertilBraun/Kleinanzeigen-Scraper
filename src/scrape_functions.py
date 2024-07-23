import requests
from bs4 import BeautifulSoup

from src.defines import BASE_URL
from src.types import Offer, User


def scrape_offer_url(url: str) -> Offer:
    response = requests.get(url)
    response.raise_for_status()  # Raises an HTTPError for bad responses (4XX, 5XX)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract offer details
    offer_id = soup.find(id='viewad-ad-id-box').find_all('li')[1].text.strip()
    offer_title = soup.find(id='viewad-title').text.strip()
    offer_description = soup.find(id='viewad-description-text').text.strip()
    offer_price = soup.find(id='viewad-price').text.strip()
    offer_location = soup.find(id='viewad-locality').text.strip()
    offer_date = soup.find(id='viewad-extra-info').div.span.text.strip()

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
        sold=False,  # TODO check if the offer is sold (doesnt seem to be possible without running JS code on the page)
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
