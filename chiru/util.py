"""
Utilities
"""
import aiohttp


async def get_file(url):
    """
    Get a file from the web using aiohttp.
    """
    with aiohttp.ClientSession() as sess:
        async with sess.get(url) as get:
            assert isinstance(get, aiohttp.ClientResponse)
            data = await get.read()
            return data