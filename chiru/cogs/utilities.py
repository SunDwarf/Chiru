"""
Utilities cog.
"""
import asyncio

import datetime
import discord
import time
from discord.ext import commands

from bot import Chiru
from override import Context


class Utilities:
    """
    Useful for tedious server things.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.group(pass_context=True)
    async def getperms(self, ctx: Context, *, number: int):
        """
        Gets the permissions of a permissions number.
        """
        perms = discord.Permissions(number)
        fmt = "```http\n"
        for name, perm in perms:
            fmt += "{}: {}\n".format(name.replace("_", " ").capitalize(), perm)

        fmt += "```"
        await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def getroleid(self, ctx: Context, role: discord.Role):
        """
        Gets the role ID associated with the role specified.
        """
        await self.bot.say("`{}`".format(role.id))

    @commands.command(pass_context=True)
    async def rolecount(self, ctx: Context, *, rolename: str):
        """
        Returns the number of people in a specified role.
        """
        role = None
        for r in ctx.server.roles:
            if r.name.lower() == rolename.lower():
                role = r
                break

        counter = 0
        for member in ctx.server.members:
            if role in member.roles:
                counter += 1

        await self.bot.say("`{}`".format(counter))

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def resetnames(self, ctx: Context):
        """
        Resets the nicknames of all members on a server (if possible).
        """
        futures = []
        for member in ctx.server.members:
            if member.top_role.position < ctx.server.me.top_role.position:
                futures.append(self.bot.change_nickname(member, None))

        results = await asyncio.gather(*futures, return_exceptions=True)

        changed = sum(1 for _ in results if not isinstance(_, Exception))

        await self.bot.say("Changed `{}` nicknames.".format(changed))

    @commands.command(pass_context=True)
    async def uptime(self, ctx: Context):
        """
        Shows the bot's uptime.
        """
        uptime = time.time() - self.bot.start_time

        m, s = divmod(uptime, 60)
        h, m = divmod(m, 60)
        formatted = "%d:%02d:%02d" % (h, m, s)

        await self.bot.say("Bot has been running for `{}`.".format(formatted))


def setup(bot: Chiru):
    bot.add_cog(Utilities(bot))
