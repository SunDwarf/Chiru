"""
Intersphinx docs.
"""
import functools
import json

from discord.ext import commands
from fuzzywuzzy.fuzz import QRatio
from logbook import Logger
from sphinx.ext import intersphinx
from fuzzywuzzy import process

from bot import Chiru
from chiru import checks

OBJECTS = [
    "https://docs.python.org/3/objects.inv",
    "http://docs.makotemplates.org/en/latest/objects.inv",
    "http://discordpy.readthedocs.io/en/latest/objects.inv",
    "https://aiohttp.readthedocs.org/en/stable/objects.inv",
    "http://flask.pocoo.org/docs/latest/objects.inv"
]


class MockSphinxApp:
    """
    Mock app used for downloading objects.inv.
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)


class Docs:
    def __init__(self, bot: Chiru):
        self.bot = bot

        # Create the MockSphinxApp.
        self._app = MockSphinxApp(self.bot.logger)

        self.invdata = {}

    async def setup(self):
        """
        Download objects.inv.
        """
        invdata = {}
        for obb in OBJECTS:
            _data = await self.bot.loop.run_in_executor(
                None, functools.partial(intersphinx.fetch_inventory, self._app, '', obb)
            )

            for kx, value in _data.items():
                if kx.startswith("std"):
                    # Ignore these, they're sphinx directives.
                    continue
                for key, subvals in value.items():
                    invdata[key] = subvals

        self.invdata = invdata

    @commands.group(pass_context=True, invoke_without_command=True)
    async def pydoc(self, ctx, *, node: str):
        """
        Looks up the pydoc of a specified item.

        This does a *fuzzy* search of the item requested.
        """
        f = functools.partial(process.extractOne, node, self.invdata.keys(), scorer=QRatio)
        item = await self.bot.loop.run_in_executor(None, f)
        if not item:
            await self.bot.say(":x: No results found.")
            return

        key, score = item

        # Get the key that was returned by the fuzzy search.
        data = self.invdata[key]

        doc, ver, url = data[0:3]
        await self.bot.say("`{}` in {} {} - <{}> (returned with score {})".format(key, doc, ver, url, score))

    @pydoc.command(pass_context=True)
    async def exact(self, ctx, *, node: str):
        """
        Does an exact search of the pydoc command specified.
        """
        data = self.invdata.get(node)
        if not data:
            await self.bot.say(":x: Could not find node with that name.")
            return

        doc, ver, url = data[0:3]
        await self.bot.say("`{}` in {} {} - <{}>".format(node, doc, ver, url))

    @pydoc.command(pass_context=True)
    @commands.check(checks.is_owner)
    async def dump(self, ctx):
        """
        Dumps pydoc data to disk.
        """
        with open("pydoc.json", 'w') as f:
            json.dump(self.invdata, f, indent=4, sort_keys=True)

        await self.bot.say("Dumped.")

    @pydoc.command(pass_context=True)
    async def sources(self, ctx):
        """
        Lists the sources that pydoc retrieves from.
        """
        base = "**Current sources:**\n"
        for source in OBJECTS:
            base += " - <{}>\n".format(source)

        await self.bot.say(base)


def setup(bot: Chiru):
    cc = Docs(bot)
    bot.loop.create_task(cc.setup())

    bot.add_cog(cc)
