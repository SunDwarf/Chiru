"""
Kyoukai web server.
"""
from kyokai import Request
from kyokai.context import HTTPRequestContext
from kyokai.app import Kyōkai
from logbook import Logger

from bot import Chiru
from .event_handlers import handlers

logger = Logger("Chiru::Commits")

kyk = Kyōkai("commits")

help_text = "Please see https://github.com/SunDwarf/Chiru/wiki/commits to see how to set up Chiru for recording " \
            "commits."


@kyk.route("/")
async def root(r: HTTPRequestContext):
    """
    Root method.
    """
    return "It works!"


async def handle_event(bot: Chiru, request: Request):
    """
    Handles a webhook event.
    """
    if not 'X-GitHub-Event' in request.headers:
        # Don't respond to non-github requests.
        logger.warn("Recieved non-github event...")
        return "", 400

    # TODO: Check secret.

    event = request.headers['X-GitHub-Event']
    # Delegate it.
    handler = handlers.get(event)
    if not handlers:
        logger.info("Recieved unhandled event {}.".format(event))
        return "Unhandled event", 200

    return await handler(bot, request)


@kyk.route("/webhook", methods=["GET", "POST"])
async def webhook(r: HTTPRequestContext):
    """
    Webhook request.
    """
    assert isinstance(r.request, Request)
    if r.request.method == "GET":
        return help_text, 200, {"Content-Type": "text/plain"}
    else:
        return await handle_event(r.request.extra["bot"], r.request)
