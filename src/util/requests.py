import aiohttp


async def get(url: str) -> str:
    """Send a GET request to the specified URL and return the response content.
    Raises an ClientResponseError for bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        async with session.get(url, ssl=False) as response:
            if response.status != 200:
                print(f'Error: {response.status} {response.reason} - {url}')
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                )
            return await response.text()


async def get_bytes(url: str) -> bytes:
    """Send a GET request to the specified URL and return the response content as bytes.
    Raises an ClientResponseError for bad responses (4XX, 5XX)."""

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        async with session.get(url, ssl=False) as response:
            if response.status != 200:
                print(f'Error: {response.status} {response.reason} - {url}')
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                )
            return await response.read()
