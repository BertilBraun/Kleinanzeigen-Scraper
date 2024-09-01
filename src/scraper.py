import os
import asyncio

from abc import abstractmethod

from src.config import OFFER_IMAGE_DIR
from src.types import Offer
from src.util import timeblock, get_bytes, run_in_batches


class BaseScraper:
    def __init__(self, offer_page_batch_size: int, max_offers_per_page: int, max_pages_to_scrape: int):
        self.offer_page_batch_size = offer_page_batch_size
        self.max_offers_per_page = max_offers_per_page
        self.max_pages_to_scrape = max_pages_to_scrape

    @abstractmethod
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        # Return only the relevant search URLs for the current scraper
        ...

    @abstractmethod
    async def scrape_offer_url(self, url: str) -> Offer:
        # Scrape the offer details from the provided offer URL
        ...

    @abstractmethod
    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str]:
        # Scrape the links to all offers from the provided search URL
        ...

    async def scrape_all_offers(self, search_urls: list[str]) -> list[Offer]:
        with timeblock('scraping all offer links'):
            all_offer_links_list = await run_in_batches(
                self.filter_relevant_urls(search_urls),
                self.offer_page_batch_size,
                self._scrape_all_offer_links_from_search_url,
                desc='Scraping offer links',
            )
        all_offer_links = [link for link in set().union(*all_offer_links_list) if link is not None and link != '']

        with timeblock(f'scraping all {len(all_offer_links)} offers'):
            return await self._scrape_all_offers_from_offer_links(all_offer_links)

    @staticmethod
    async def scrape_offer_images(offers: list[Offer], offer_page_batch_size: int) -> None:
        async def _scrape_offer_images(offer: Offer) -> None:
            offer_folder = f'{OFFER_IMAGE_DIR}/{offer.id}/'

            if os.path.exists(offer_folder):
                return

            os.makedirs(offer_folder, exist_ok=True)

            for idx, image_url in enumerate(offer.image_urls):
                image_bytes = await get_bytes(image_url)
                with open(offer_folder + f'{idx}.jpg', 'wb') as file:
                    file.write(image_bytes)

        await run_in_batches(
            offers,
            offer_page_batch_size,
            _scrape_offer_images,
            desc='Scraping offer images',
        )

    async def _scrape_all_offer_links_from_search_url(self, search_url: str) -> list[str]:
        all_offer_links: set[str] = set()

        async def after_batch(urls: list[list[str]]) -> bool:
            for url_list in urls:
                all_offer_links.update(url_list)
            return len(all_offer_links) % self.max_offers_per_page != 0

        await run_in_batches(
            list(range(1, self.max_pages_to_scrape)),
            self.offer_page_batch_size,
            lambda page: self.scrape_offer_links_from_search_url(search_url.format(page)),
            desc=None,
            after_batch=after_batch,
        )

        return list(all_offer_links)

    async def _scrape_all_offers_from_offer_links(self, all_offer_links: list[str]) -> list[Offer]:
        async def after_batch(_: list[Offer]) -> bool:
            await asyncio.sleep(1)
            return True

        return [
            offer
            for offer in await run_in_batches(
                all_offer_links,
                self.offer_page_batch_size,
                self.scrape_offer_url,
                desc='Scraping offers',
                after_batch=after_batch,
            )
            if offer is not None
        ]
