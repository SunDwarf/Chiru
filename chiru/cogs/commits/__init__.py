"""
Commits main file.
"""
from logbook import Logger

from bot import Chiru
from .web import kyk

logger = Logger("Chiru")


class Commits(object):
    """
    Commit bot.
    """

    def __init__(self, bot: Chiru):
        """
        Load the Kyoukai built-in web server.
        """
        self.bot = bot

    def __unload(self):
        """
        Close the web server.
        """
        logger.info("Closing Kyoukai server.")
        kyk.component.server.close()


def setup(bot: Chiru):
    bot.add_cog(Commits(bot))

    # Start Kyoukai.
    bot.loop.create_task(kyk.start())