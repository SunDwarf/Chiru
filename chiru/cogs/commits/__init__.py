"""
Commits main file.
"""
import aiohttp
import aioredis
import random
import string
from kyokai import Request

from discord.ext import commands
from kyokai.context import HTTPRequestContext
from logbook import Logger

from bot import Chiru
from override import Context
from .web import kyk

logger = Logger("Chiru::Commits")


class Commits(object):
    """
    Commit bot.
    """

    def __init__(self, bot: Chiru):
        """
        Load the Kyoukai built-in web server.
        """
        self.bot = bot

    async def _kyk_before_request(self, r: HTTPRequestContext):
        assert isinstance(r.request, Request)
        r.request.extra["bot"] = self.bot
        return r.request

    def __unload(self):
        """
        Close the web server.
        """
        logger.info("Closing Kyoukai server.")
        kyk.component.server.close()

    @commands.group(pass_context=True, invoke_without_command=True)
    async def link(self, ctx: Context):
        """
        Link the Commits of a repository to a specific repo.

        This base command will just show the current links for this channel.
        """
        async with (await self.bot.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            # Get the set of items.
            s = await conn.smembers("commit_{}".format(ctx.channel.id))

        if len(s) == 0:
            await self.bot.say("**Not currently tracking any repos for this channel.**")
            return

        s = {_.decode() for _ in s}

        t = "**Currently tracking {} repo(s) for this channel:**\n".format(len(s))
        t += '\n'.join(s)

        await self.bot.say(t)

    async def _get_ip(self):
        c = self.bot.config.get("commitbot_ip")
        if c:
            return c

        # Use HTTPbin to get our own IP.
        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://httpbin.org/ip") as r:
                assert isinstance(r, aiohttp.ClientResponse)
                data = await r.json()
                return data["origin"]

    @link.command(pass_context=True)
    async def add(self, ctx: Context, *, repo: str):
        """
        Add a repository link to the channel.

        This link must be in the format of `Username/Repository`.
        """
        needs_webhook = True
        async with (await self.bot.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            # Store the forward and reverse links.
            await conn.sadd("commit_{}".format(ctx.channel.id), repo)
            if await conn.smembers("commit_{}".format(repo)):
                # The repo already has a webhook set up, evidently.
                # Don't attempt to re-add the web hook.
                needs_webhook = False
            await conn.sadd("commit_{}".format(repo), ctx.channel.id)

            logger.info("Creating webhook -> {}".format(needs_webhook))
            if not needs_webhook:
                await self.bot.say("Linked `{}` to `{}`.".format(repo, ctx.channel.name))
                return
            else:
                await self.bot.say(
                    "Linked `{}` to `{}`. PMing you with webhook creation information.".format(repo, ctx.channel.name)
                )
                # Generate a random secret.
                r = ''.join(
                    random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(16))
                await conn.set("commit_{}_secret".format(repo), r)

                # Format the webhook url.
                if self.bot.config.get("commitbot"):
                    cc = self.bot.config["commitbot"]
                    _addr = cc.get("hookaddr")
                    if _addr:
                        addr = _addr
                    else:
                        addr = "http://{}{}/webhook".format(
                            cc.get("host"), ':' + cc.get("port") if cc.get("port") else ''
                        )
                else:
                    ip = await self._get_ip()
                    port = kyk.component.port
                    addr = "http://{}:{}/webhook".format(ip, port)

                await self.bot.send_message(ctx.author, "To complete commit linking, add a new webhook to your repo.\n"
                                                        "The webhook should point to `{}`, "
                                                        "and must have the "
                                                        "secret of `{}`.".format(addr, r))

    @link.command(pass_context=True)
    async def remove(self, ctx: Context, *, repo: str):
        """
        Remove a repository link.
        """
        async with (await self.bot.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            removed = await conn.srem("commit_{}".format(repo), ctx.channel.id.encode())
            if not removed:
                await self.bot.say(":x: This channel was not linked to that repo.")
                return
            # Otherwise, remove it from `commit_channelid` too.
            await conn.srem("commit_{}".format(ctx.channel.id), repo.encode())
            # Check if that repo is linked anywhere
            members = await conn.smembers("commit_{}".format(repo))
            if not members or not len(members):
                await conn.delete("commit_{}_secret".format(repo))

            await self.bot.say(":heavy_check_mark: Unlinked repo `{}` from `{}`.".format(repo, ctx.channel.name))


def setup(bot: Chiru):
    cog = Commits(bot)
    bot.add_cog(cog)

    # Start Kyoukai.
    logger.info("Loading Kyoukai web server for commits.")
    kyk.before_request(cog._kyk_before_request)
    bot.loop.create_task(kyk.start(port=5555))
