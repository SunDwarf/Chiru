"""
Kyoukai web server.
"""
from kyokai import Request
from kyokai.app import Kyōkai

kyk = Kyōkai("commits")


@kyk.route("/")
async def root(r: Request):
    """
    Root method.
    """
    return "It works!"
