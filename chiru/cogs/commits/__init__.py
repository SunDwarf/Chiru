"""
Commits main file.
"""
import aiohttp
import aioredis

from discord.ext import commands
from logbook import Logger

from bot import Chiru
from chiru import checks
from chiru.cogs.commits.web import bp
from override import Context

logger = Logger("Chiru::Commits")


class Commits(object):
    """
    Commit bot.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def link(self, ctx: Context):
        """
        Link the Commits of a repository to a specific repo.

        This base command will just show the current links for this channel.
        """
        repos = await self.bot.db.get_repos_for_channel(ctx.channel)

        if len(repos) == 0:
            await self.bot.say("**Not currently tracking any repos for this channel.**")
            return

        s = {repo.repo_name for repo in repos}

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
    @commands.check(checks.has_manage_channels)
    async def add(self, ctx: Context, *, repo: str):
        """
        Add a repository link to the channel.

        You must have `Manage Channels` to use this command.

        This link must be in the format of `Username/Repository`.
        """

        # lol easy command
        link, created = await self.bot.db.create_link(ctx.channel, repo)

        if not created:
            await self.bot.say(":heavy_check_mark: Linked `{}` to `{}`.".format(repo, ctx.channel.name))
            return

        # Give instructions on how to link the repo.
        await self.bot.say(
            "Linked `{}` to `{}`. PMing you with webhook creation information.".format(repo, ctx.channel.name)
        )
        secret = link.secret

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
            port = self.bot._webserver.component.port
            addr = "http://{}:{}/webhook".format(ip, port)

        fmt = "To complete commit linking, add a new webhook to your repo.\n The webhook should point to `{}`, " \
              "and must have the secret of `{}`.".format(addr, secret)

        await self.bot.send_message(ctx.author, fmt)

    @link.command(pass_context=True)
    @commands.check(checks.has_manage_channels)
    async def remove(self, ctx: Context, *, repo: str):
        """
        Remove a repository link.

        You must have `Manage Channels` to use this command.
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
    logger.info("Registering blueprint with built-in webserver.")
    bot.register_blueprint(bp)
