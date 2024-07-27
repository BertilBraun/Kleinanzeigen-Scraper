from abc import abstractmethod
import asyncio

from src.types import Offer
from src.util import log_all_exceptions, timeblock


class BaseScraper:
    def __init__(self, offer_page_batch_size: int, max_offers_per_page: int):
        self.offer_page_batch_size = offer_page_batch_size
        self.max_offers_per_page = max_offers_per_page

    @abstractmethod
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        ...

    async def scrape_all_offers(self, search_urls: list[str]) -> list[Offer]:
        all_offer_links: set[str] = set()
        for search_url in self.filter_relevant_urls(search_urls):
            with timeblock(f'scraping all offer links from {search_url} from DailyDose'):
                all_offer_links.update(await self._scrape_all_offer_links_from_search_url(search_url))

        with timeblock(f'scraping all {len(all_offer_links)} offers from DailyDose'):
            return await self._scrape_all_offers_from_offer_links(list(all_offer_links))

    @abstractmethod
    async def scrape_offer_url(self, url: str) -> Offer:
        ...

    @abstractmethod
    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str]:
        ...

    async def _scrape_all_offer_links_from_search_url(self, search_url: str) -> list[str]:
        all_offer_links: set[str] = set()

        for batch_start in range(1, 100, self.offer_page_batch_size):
            batch_end = batch_start + self.offer_page_batch_size
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
        return [await self.scrape_offer_url(url) for url in all_offer_links]

        offers: list[Offer] = []
        for batch_start in range(0, len(all_offer_links), self.offer_page_batch_size):
            batch_end = min(batch_start + self.offer_page_batch_size, len(all_offer_links))
            offer_futures = [self.scrape_offer_url(url) for url in all_offer_links[batch_start:batch_end]]
            for offer in asyncio.as_completed(offer_futures):
                with log_all_exceptions('while scraping offer'):
                    offers.append(await offer)

            await asyncio.sleep(30)
        return offers
