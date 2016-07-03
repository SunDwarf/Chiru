"""
Fun commands.
"""
from discord.ext import commands

from bot import Chiru
from override import Context


class Fun(object):
    """
    aaa
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    async def stats(self, ctx: Context):
        """
        Show stats about the bot.
        """
        await self.bot.say(
            "Currently connected to `{}` servers, with `{}` channels and `{}` users.".format(
                len(self.bot.servers), len([x for x in self.bot.get_all_channels()]),
                len([x for x in self.bot.get_all_members()])
            )
        )


def setup(bot: Chiru):
    bot.add_cog(Fun(bot))
