"""
Utilities cog.
"""
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


def setup(bot: Chiru):
    bot.add_cog(Utilities(bot))
