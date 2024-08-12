from abc import abstractmethod
import asyncio
from math import ceil
import os

from tqdm import tqdm

from src.config import OFFER_IMAGE_DIR
from src.requests import get_bytes
from src.types import Offer
from src.util import log_all_exceptions, timeblock


class BaseScraper:
    def __init__(self, offer_page_batch_size: int, max_offers_per_page: int, max_pages_to_scrape: int):
        self.offer_page_batch_size = offer_page_batch_size
        self.max_offers_per_page = max_offers_per_page
        self.max_pages_to_scrape = max_pages_to_scrape

    @abstractmethod
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        ...

    async def scrape_all_offers(self, search_urls: list[str]) -> list[Offer]:
        with timeblock('scraping all offer links'):
            all_offer_links_list = await asyncio.gather(
                *[
                    self._scrape_all_offer_links_from_search_url(search_url)
                    for search_url in self.filter_relevant_urls(search_urls)
                ]
            )
        all_offer_links = set().union(*all_offer_links_list)

        with timeblock(f'scraping all {len(all_offer_links)} offers'):
            return await self._scrape_all_offers_from_offer_links(list(all_offer_links))

    @abstractmethod
    async def scrape_offer_url(self, url: str) -> Offer:
        ...

    @abstractmethod
    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str]:
        ...

    @staticmethod
    async def scrape_offer_images(offers: list[Offer], offer_page_batch_size: int) -> None:
        async def _scrape_offer_images(offer: Offer) -> None:
            offer_folder = f'{OFFER_IMAGE_DIR}/{offer.id}/'

            os.makedirs(offer_folder, exist_ok=True)

            for idx, image_url in enumerate(offer.image_urls):
                image_bytes = await get_bytes(image_url)
                with open(offer_folder + f'{idx}.jpg', 'wb') as file:
                    file.write(image_bytes)

        for batch_start in tqdm(
            range(0, len(offers), offer_page_batch_size),
            desc='Scraping offer images',
            unit='offer batch',
            total=ceil(len(offers) / offer_page_batch_size),
        ):
            batch_end = min(batch_start + offer_page_batch_size, len(offers))
            offer_futures = [_scrape_offer_images(offer) for offer in offers[batch_start:batch_end]]
            for offer in asyncio.as_completed(offer_futures):
                with log_all_exceptions('while scraping offer images'):
                    await offer

    async def _scrape_all_offer_links_from_search_url(self, search_url: str) -> list[str]:
        all_offer_links: set[str] = set()

        for batch_start in range(1, 100, self.offer_page_batch_size):
            batch_end = min(batch_start + self.offer_page_batch_size, self.max_pages_to_scrape)
            offer_link_futures = [
                self.scrape_offer_links_from_search_url(search_url.format(page))
                for page in range(batch_start, batch_end)
            ]
            for offer_links in asyncio.as_completed(offer_link_futures):
                with log_all_exceptions('while scraping offer links'):
                    all_offer_links.update(await offer_links)

            if len(all_offer_links) < self.max_offers_per_page * (batch_end - 1):
                break

        return list(all_offer_links)

    async def _scrape_all_offers_from_offer_links(self, all_offer_links: list[str]) -> list[Offer]:
        offers: list[Offer] = []
        for batch_start in tqdm(
            range(0, len(all_offer_links), self.offer_page_batch_size),
            desc='Scraping offers',
            unit='offer batch',
            total=ceil(len(all_offer_links) / self.offer_page_batch_size),
        ):
            batch_end = min(batch_start + self.offer_page_batch_size, len(all_offer_links))
            offer_futures = [self.scrape_offer_url(url) for url in all_offer_links[batch_start:batch_end]]
            for offer in asyncio.as_completed(offer_futures):
                with log_all_exceptions('while scraping offer'):
                    offers.append(await offer)

            await asyncio.sleep(1)

        return offers
