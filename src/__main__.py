from src.scrape_functions import scrape_offer_links_from_search_url, scrape_offer_url
from src.defines import BASE_URL
from src.util import json_dumper

if __name__ == '__main__':
    WINDSURF_SEARCH_URL = BASE_URL + '/s-karlsruhe/seite:{}/windsurfen/k0l9186r50'
    OUTPUT_JSON_DATA_FILE = 'data.json'

    with json_dumper(OUTPUT_JSON_DATA_FILE) as dumper:
        for page in range(1, 3):
            print(f'Scraping page {page}...')
            offer_links = scrape_offer_links_from_search_url(WINDSURF_SEARCH_URL.format(page))
            print(f'Found {len(offer_links)} offers on page {page}.\n')

            for url in offer_links:
                offer, user = scrape_offer_url(url)
                dumper({'offer': offer, 'user': user})
                print(offer)
                print(user)
                print()
