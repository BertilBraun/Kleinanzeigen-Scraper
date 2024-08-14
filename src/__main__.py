import json
import asyncio

from src.display import to_excel
from src.extract import extract_offer_details
from src.scraper import BaseScraper
from src.scraper_dailydose import ScraperDailyDose
from src.scraper_kleinanzeigen import ScraperKleinanzeigen
from src.config import CURRENT_OFFERS_FILE, DB_FILE, DO_REQUERY_OLD_OFFERS, INTEREST_LOCATIONS, WINDSURF_SEARCH_URLS
from src.lat_long import distance, extract_lat_long, plz_to_lat_long
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
    ALL_SCRAPERS: list[BaseScraper] = [
        ScraperKleinanzeigen(max_pages_to_scrape=10),
        ScraperDailyDose(max_pages_to_scrape=5),
    ]
    for scraper in ALL_SCRAPERS:
        all_offers.extend(await scraper.scrape_all_offers(WINDSURF_SEARCH_URLS))

    dump_json(all_offers, CURRENT_OFFERS_FILE)

    database_entries = load_database(DB_FILE)

    new_offers, old_offers, sold_offers = partition_offers(all_offers, database_entries)

    filtered_new_offers: list[Offer] = []
    for offer in new_offers:
        if not offer.location.strip():
            print(f'Offer: {offer.title} has no location - check manually: {offer.link}')
            continue

        lat_lon = await extract_lat_long(offer.location)

        if any(distance(lat_lon, plz_to_lat_long(location)) < radius for location, radius, _ in INTEREST_LOCATIONS):
            filtered_new_offers.append(offer)

    print(f'Total new offers: {len(new_offers)}')
    print(f'Filtered new offers: {len(filtered_new_offers)}')
    print(f'Old offers: {len(old_offers)}')
    print(f'Sold offers: {len(sold_offers)}')

    for entry in sold_offers:
        entry.metadata.offer.sold = True

    for entry in new_offers:
        entry.sold = False

    for offer, entry in old_offers:
        entry.metadata.offer.sold = False

    with timeblock('updating old offers'):
        for offer, entry in old_offers:
            title_is_longer = len(offer.title) > len(entry.metadata.offer.title)
            description_is_longer = len(offer.description) > len(entry.metadata.offer.description)
            if (title_is_longer or description_is_longer) and DO_REQUERY_OLD_OFFERS:
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
        await BaseScraper.scrape_offer_images(filtered_new_offers, 5)

    # store everything in the database
    new_database_entries = extracted_details + database_entries
    dump_json(new_database_entries, DB_FILE)

    path = await to_excel(new_database_entries)
    print(f'Data saved to: {path}')

    # TODO Liste an stuff nach denen man sucht, GPT die neuen offers und die gesuchen items geben und ihn filtern lassen, welche davon relevant sind - daraus dann eine Notification

    with open(R'C:\Users\berti\OneDrive\Desktop\kleinanzeigen_scraped.txt', 'w') as f:
        f.write(f'New Offers have been scraped and {len(new_database_entries)} have been added\n\n')
        f.write('New offers:\n')
        for entry in extracted_details:
            f.write('-' * 30 + f' New offer: {entry.metadata.type} ' + '-' * 30 + '\n')
            for name, value in (await entry.to_excel()).items():
                if name not in ['All other offers', 'Date', 'Location', 'Sold', 'VB']:
                    f.write(f'{name}: {value.value}\n')
            f.write('-' * 80 + '\n')


if __name__ == '__main__':
    # asyncio.run(to_excel(load_database(DB_FILE)))

    asyncio.run(main())
