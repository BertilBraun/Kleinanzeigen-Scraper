import json
import asyncio

from src.display import to_excel
from src.extract import extract_offer_details
from src.lat_long import distance, extract_plz, plz_to_lat_long
from src.scraper import BaseScraper
from src.scraper_dailydose import ScraperDailyDose
from src.scraper_kleinanzeigen import ScraperKleinanzeigen
from src.config import CURRENT_OFFERS_FILE, DB_FILE, INTEREST_LOCATIONS, WINDSURF_SEARCH_URLS
from src.types import DatabaseFactory, Entry, Offer
from src.util import dump_json, timeblock


def load_database(path: str) -> list[Entry]:
    try:
        with open(path, 'r') as file:
            return DatabaseFactory.from_json(json.load(file))
    except FileNotFoundError:
        return []


def partition_offers(
    all_current_offers: list[Offer], database_entries: list[Entry]
) -> tuple[list[Offer], list[tuple[Offer, Entry]], list[Entry]]:
    # partition into: new offers which are not yet in the database, offers which are already in the database but still in the current offers, and offers which are no longer in the current offers
    new_offers: list[Offer] = []

    for offer in all_current_offers:
        if not any(entry.metadata.offer.id == offer.id for entry in database_entries):
            new_offers.append(offer)

    old_offers: list[tuple[Offer, Entry]] = []
    sold_offers: list[Entry] = []

    for entry in database_entries:
        if not any(offer.id == entry.metadata.offer.id for offer in all_current_offers):
            sold_offers.append(entry)
        else:
            offer = next(offer for offer in all_current_offers if offer.id == entry.metadata.offer.id)
            old_offers.append((offer, entry))

    return new_offers, old_offers, sold_offers


async def main():
    all_offers: list[Offer] = []
    ALL_SCRAPERS: list[BaseScraper] = [ScraperKleinanzeigen(), ScraperDailyDose()]
    for scraper in ALL_SCRAPERS:
        all_offers.extend(await scraper.scrape_all_offers(WINDSURF_SEARCH_URLS))

    dump_json(all_offers, CURRENT_OFFERS_FILE)

    database_entries = load_database(DB_FILE)

    new_offers, old_offers, sold_offers = partition_offers(all_offers, database_entries)

    filtered_new_offers: list[Offer] = []
    for offer in new_offers:
        if plz := extract_plz(offer.location):
            # not all offers from dailydose.de have a plz in the location
            lat_lon = plz_to_lat_long(plz)
            if any(distance(lat_lon, location) < radius for location, radius in INTEREST_LOCATIONS):
                filtered_new_offers.append(offer)
        else:
            print(f'Offer: {offer.title} has no postal code - check manually: {offer.link}')

    print(f'New offers: {len(filtered_new_offers)}')
    print(f'Old offers: {len(old_offers)}')
    print(f'Sold offers: {len(sold_offers)}')

    for entry in sold_offers:
        entry.metadata.offer.sold = True

    with timeblock('updating old offers'):
        for offer, entry in old_offers:
            title_is_longer = len(offer.title) > len(entry.metadata.offer.title)
            description_is_longer = len(offer.description) > len(entry.metadata.offer.description)
            if title_is_longer or description_is_longer:
                print(
                    f'Offer {offer.id} has a longer title or description than the one in the database. Re-extracting the details.'
                )
                if title_is_longer:
                    print(f'Old title: {entry.metadata.offer.title}')
                    print(f'New title: {offer.title}')
                if description_is_longer:
                    print(f'Old description: {entry.metadata.offer.description}')
                    print(f'New description: {offer.description}')
                # reextract the offer details via llm
                new_entry_details = await extract_offer_details(offer)
                for key, value in new_entry_details.__dict__.items():
                    setattr(entry, key, value)
            # update the entry in the database
            offer.scraped_on = entry.metadata.offer.scraped_on
            entry.metadata.offer = offer

    # extract the details of the new offers
    with timeblock('extracting the details of the new offers'):
        extracted_details = await asyncio.gather(*[extract_offer_details(offer) for offer in filtered_new_offers])

    # store everything in the database
    new_database_entries = extracted_details + database_entries
    dump_json(new_database_entries, DB_FILE)

    path = to_excel(new_database_entries)
    print(f'Data saved to: {path}')

    print('New offers:')
    for entry in extracted_details:
        print('-' * 30 + f' New offer: {entry.metadata.type} ' + '-' * 30)
        for name, value in entry.to_excel().items():
            if name not in ['All other offers', 'Date', 'Location', 'Sold', 'VB']:
                print(f'{name}: {value.value}')
        print('-' * 80)


if __name__ == '__main__':
    # to_excel(load_database(DB_FILE))
    asyncio.run(main())
