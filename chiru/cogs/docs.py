"""
Intersphinx docs.

_requirements:: ['sphinx', 'fuzzywuzzy']
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

        self._item_lengths = {}

    async def setup(self):
        """
        Download objects.inv.
        """
        invdata = {}
        for name, obb in self.bot.config.get("docs", {}).items():
            self.bot.logger.info("Fetching Pydocs for {}...".format(name))
            _data = await self.bot.loop.run_in_executor(
                None, functools.partial(intersphinx.fetch_inventory, self._app, '', obb)
            )

            if _data is None:
                self.bot.logger.error("Failed to download Pydoc source {}".format(obb))
                continue

            # Set the invdata of the current pydoc library
            invdata[name] = {}

            self._item_lengths[name] = 0

            for kx, value in _data.items():
                if kx.startswith("std"):
                    # Ignore these, they're sphinx directives.
                    continue
                for key, subvals in value.items():
                    self._item_lengths[name] += 1
                    invdata[name][key] = subvals

        self.invdata = invdata

    @commands.group(pass_context=True, invoke_without_command=True)
    async def pydoc(self, ctx, *, node: str):
        """
        Looks up the pydoc of a specified item.

        This does a *fuzzy* search of the item requested.
        """
        def _get_items():
            for v in self.invdata.values():
                for subv in v:
                    yield subv

        f = functools.partial(process.extractOne, node, _get_items())
        item = await self.bot.loop.run_in_executor(None, f)
        if not item:
            await self.bot.say(":x: No results found.")
            return

        key, score = item

        # Get the key that was returned by the fuzzy search.
        data = ["??", "??", "??"]
        for name, v in self.invdata.items():
            try:
                data = v[key]
            except KeyError:
                continue
            else:
                break

        doc, ver, url = data[0:3]
        await self.bot.say("`{}` in {} {} - <{}> (returned with score {})".format(key, doc, ver, url, score))

    @pydoc.command(pass_context=True)
    async def multi(self, ctx, limit: int, *, node: str):
        """
        Looks up the fuzzy pydoc of a specified item.

        Limit defines the number of items you wish to return (up to 10).
        """
        def _get_items():
            for v in self.invdata.values():
                for subv in v:
                    yield subv

        limit = min(10, limit)
        f = functools.partial(process.extractBests, node, _get_items(), limit=limit)
        item = await self.bot.loop.run_in_executor(None, f)
        if not item:
            await self.bot.say(":x: No results found.")
            return

        base = "**Pydoc results:**\n"

        for result in item:
            key, score = result

            # Get the key that was returned by the fuzzy search.
            data = ["??", "??", "??"]
            for name, v in self.invdata.items():
                try:
                    data = v[key]
                except KeyError:
                    continue
                else:
                    break

            doc, ver, url = data[0:3]
            base += "`{}` in {} {} - <{}> (returned with score {})\n".format(key, doc, ver, url, score)

        await self.bot.say(base)

    @pydoc.command(pass_context=True)
    async def module(self, ctx, module: str, *, node: str):
        """
        Fetches a pydoc from a specified module and node.
        """
        items = self.invdata.get(module.lower(), {})
        f = functools.partial(process.extractOne, node, items)
        item = await self.bot.loop.run_in_executor(None, f)

        if not item:
            await self.bot.say(":x: No results found.")
            return

        data, score, key = item

        doc, ver, url = data[0:3]

        await self.bot.say("`{}` in {} {} - <{}> (returned with score {})".format(key, doc, ver, url, score))

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
        for source in self.bot.config.get("docs", []):
            try:
                base += " - <{}> (`{}` items)\n".format(source, self._item_lengths[source])
            except KeyError:
                continue

        base += "\nTracking `{}` out of `{}` valid sources.".format(len(self.bot.config.get("docs", [])),
                                                                    len(self._item_lengths))

        base += "\nCurrently tracking `{}` items.".format(len(self.invdata))

        await self.bot.say(base)


def setup(bot: Chiru):
    cc = Docs(bot)
    bot.loop.create_task(cc.setup())

    bot.add_cog(cc)
