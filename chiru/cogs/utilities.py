"""
Utilities cog.
"""
import asyncio
import discord
from discord.ext import commands

from bot import Chiru
from override import Context


class Utilities:
    """
    Useful for tedious server things.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

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


def setup(bot: Chiru):
    bot.add_cog(Utilities(bot))
