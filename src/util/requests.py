import time
import aiohttp


class GETError(Exception):
    """Custom exception for GET request errors."""


async def get(url: str) -> str:
    """Send a GET request to the specified URL and return the response content.
    Raises an GETError for repeated bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        for i in range(5):
            try:
                async with session.get(url, ssl=False) as response:
                    response.raise_for_status()  # Raise an error for bad responses
                    return await response.text()
            except:
                print(f'Retrying GET request: {url}')
                time.sleep(60 * i)  # Exponential backoff

        print(f'Failed to fetch URL after retries: {url}')
        raise GETError(f'Failed to fetch URL: {url}')


async def get_bytes(url: str) -> bytes:
    """Send a GET request to the specified URL and return the response content as bytes.
    Raises an GETError for repeated bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        for i in range(5):
            try:
                async with session.get(url, ssl=False) as response:
                    response.raise_for_status()
                    return await response.read()
            except:
                print(f'Retrying GET request: {url}')
                time.sleep(60 * i)  # Exponential backoff

        print(f'Failed to fetch URL after retries: {url}')
        raise GETError(f'Failed to fetch URL: {url}')
