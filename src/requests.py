import aiohttp


async def get(url: str) -> str:
    """Send a GET request to the specified URL and return the response content.
    Raises an HTTPError for bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        async with session.get(url) as response:
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX, 5XX)
            return await response.text()


async def get_bytes(url: str) -> bytes:
    """Send a GET request to the specified URL and return the response content as bytes.
    Raises an HTTPError for bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        async with session.get(url) as response:
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX, 5XX)
            return await response.read()
