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


def safe_roles(roles: list):
    names = []
    for role in roles:
        if role.name == "@everyone":
            names.append("@​everyone")  # There is an invisible space here, u200b.
        else:
            names.append(role.name)

    return names
