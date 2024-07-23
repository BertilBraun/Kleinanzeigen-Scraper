from src.scrape_functions import scrape_offer_links_from_search_url, scrape_offer_url
from src.defines import BASE_URL
from src.util import json_dumper

if __name__ == '__main__':
    WINDSURF_SEARCH_URL = BASE_URL + '/s-karlsruhe/seite:{}/windsurfen/k0l9186r50'
    OUTPUT_JSON_DATA_FILE = 'data.json'

    with json_dumper(OUTPUT_JSON_DATA_FILE) as dumper:
        for page in range(1, 3):  # TODO fetch the number of pages from the search page
            print(f'Scraping page {page}...')
            offer_links = scrape_offer_links_from_search_url(WINDSURF_SEARCH_URL.format(page))  # TODO handle exceptions
            print(f'Found {len(offer_links)} offers on page {page}.\n')

            for url in offer_links:
                offer, user = scrape_offer_url(url)  # TODO handle exceptions
                dumper({'offer': offer, 'user': user})
                print(offer)
                print(user)
                print()

    # TODO process the offers using a LLM model for relevance, extraction of type (full set, sail, board, mast, boom, etc.), extraction of details (square meters, length, RDM/SDM, etc.), wheather the offered item was repaired, etc.
    # TODO store the processed data in a database
    # TODO update the stored data in case the offer changes (for example, the price is reduced, the item is sold, etc.)
    # TODO proper display of the available offers (in a web interface?)
