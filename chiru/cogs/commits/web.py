"""
Kyoukai web server.
"""
from kyokai import Request
from kyokai.context import HTTPRequestContext
from kyokai.app import Kyōkai

kyk = Kyōkai("commits")

help_text = "Please see https://github.com/SunDwarf/Chiru/wiki/commits to see how to set up Chiru for recording " \
            "commits."


@kyk.route("/")
async def root(r: HTTPRequestContext):
    """
    Root method.
    """
    return "It works!"


@kyk.route("/webhook", methods=["GET", "POST"])
async def webhook(r: HTTPRequestContext):
    """
    Webhook request.
    """
    assert isinstance(r.request, Request)
    if r.request.method == "GET":
        return help_text, 200, {"Content-Type": "text/plain"}