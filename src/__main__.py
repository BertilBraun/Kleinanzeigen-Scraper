import json
import asyncio


from src.display import to_excel
from src.extract import extract_offer_details
from src.scraper import BaseScraper
from src.scraper_dailydose import ScraperDailyDose
from src.scraper_kleinanzeigen import ScraperKleinanzeigen
from src.config import (
    CURRENT_OFFERS_FILE,
    DB_FILE,
    DO_REQUERY_OLD_OFFERS,
    EMAILS_TO_NOTIFY,
    INTEREST_LOCATIONS,
    INTERESTS,
    WINDSURF_SEARCH_URLS,
)
from src.lat_long import distance, extract_lat_long, plz_to_lat_long
from src.types import DatabaseFactory, Entry, Offer, list_entries_of_type
from src.types_to_search import ALL_TYPES
from src.util import timeblock, dump_json, send_mail, sync_gpt_request, date_str


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


async def filter_based_on_location(new_offers: list[Offer]) -> list[tuple[Offer, tuple[float, float]]]:
    filtered_new_offers: list[tuple[Offer, tuple[float, float]]] = []

    for offer in new_offers:
        if not offer.location.strip():
            print(f'Offer: {offer.title} has no location - check manually: {offer.link}')
            continue

        lat_long = await extract_lat_long(offer.location)

        if any(distance(lat_long, plz_to_lat_long(location)) < radius for location, radius, _ in INTEREST_LOCATIONS):
            filtered_new_offers.append((offer, lat_long))

    return filtered_new_offers


def update_sold_status(
    new_offers: list[Offer],
    old_offers: list[tuple[Offer, Entry]],
    sold_offers: list[Entry],
) -> None:
    for entry in sold_offers:
        entry.metadata.offer.sold = True

    for entry in new_offers:
        entry.sold = False

    for offer, entry in old_offers:
        entry.metadata.offer.sold = False


async def extract_new_offer_details(filtered_new_offers: list[tuple[Offer, tuple[float, float]]]) -> list[Entry]:
    with timeblock('extracting the details of the new offers'):
        extracted_details = await asyncio.gather(
            *[extract_offer_details(offer, lat_long) for offer, lat_long in filtered_new_offers]
        )
        await BaseScraper.scrape_offer_images([offer for offer, _ in filtered_new_offers], 5)

    return extracted_details


async def update_old_offers(old_offers: list[tuple[Offer, Entry]]) -> None:
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
                new_entry_details = await extract_offer_details(offer, entry.metadata.lat_long)
                for key, value in new_entry_details.__dict__.items():
                    setattr(entry, key, value)
            # update the entry in the database
            offer.scraped_on = entry.metadata.offer.scraped_on
            entry.metadata.offer = offer


def is_entry_interesting(entry: Entry, type_name: str, interest: str) -> bool:
    success, res = sync_gpt_request(
        [
            {
                'role': 'system',
                'content': 'You are a helpful assistant who is going to help me filter new windsurfing offers. Please only respond with "yes" or "no". Your job is to tell me if the offer is interesting or not.',
            },
            {
                'role': 'user',
                'content': f"""The following offer is a new windsurfing offer:
{get_entry_details_readable(entry)}
I am currently interested in the following {type_name}s: {interest}
Reply with "yes" if the offer is interesting, otherwise reply with "no".""",
            },
        ]
    )

    return success and res.lower() == 'yes'


def filter_interesting_entries_using_gpt(entries: list[Entry]) -> tuple[str, int]:
    # Liste an stuff nach denen man sucht, GPT die neuen offers und die gesuchen items geben und ihn filtern lassen, welche davon relevant sind - daraus dann eine Notification

    interesting_entries = ''
    number_of_interesting_entries = 0

    for type_ in ALL_TYPES:
        if not (interest := INTERESTS().get(type_, None)):
            continue

        interesting_entries_of_this_type = [
            entry
            for entry in list_entries_of_type(entries, type_)
            if is_entry_interesting(entry, type_.__name__, interest)
        ]

        if interesting_entries_of_this_type:
            interesting_entries += f'{type_.__name__}s:\n'
            for entry in interesting_entries_of_this_type:
                interesting_entries += get_entry_details_readable(entry)
            interesting_entries += '=' * 80 + '\n\n\n'

        number_of_interesting_entries += len(interesting_entries_of_this_type)

    return interesting_entries, number_of_interesting_entries


def get_entry_details_readable(entry: Entry) -> str:
    text = '-' * 30 + f' New offer: {entry.metadata.offer.title} ' + '-' * 30 + '\n'
    for name, value in entry.to_excel(do_add_metadata=False).items():
        text += f'{name}: {value.value}\n'
    text += f'Link: {entry.metadata.offer.link}\n'
    text += f'Price: {entry.metadata.offer.price}\n'
    text += '-' * 80 + '\n'
    return text


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

    filtered_new_offers = await filter_based_on_location(new_offers)

    print(f'Total new offers: {len(new_offers)}')
    print(f'Filtered new offers: {len(filtered_new_offers)}')
    print(f'Old offers: {len(old_offers)}')
    print(f'Sold offers: {len(sold_offers)}')

    update_sold_status(new_offers, old_offers, sold_offers)

    await update_old_offers(old_offers)

    # extract the details of the new offers
    extracted_details = await extract_new_offer_details(filtered_new_offers)

    # store everything in the database
    new_database_entries = extracted_details + database_entries
    dump_json(new_database_entries, DB_FILE)

    path = to_excel(new_database_entries)
    print(f'Data saved to: {path}')

    interesting_entries, number_of_interesting_entries = filter_interesting_entries_using_gpt(extracted_details)

    if number_of_interesting_entries:
        subject = f'New windsurfing offers ({number_of_interesting_entries}) on {date_str()}'
        text = f'New offers:\n{interesting_entries}'

        print(f'Sending mail with subject: {subject}\nText:\n{text}')
        send_mail(subject, text, EMAILS_TO_NOTIFY)
    else:
        print('No interesting offers found')


if __name__ == '__main__':
    # to_excel(load_database(DB_FILE))

    asyncio.run(main())
