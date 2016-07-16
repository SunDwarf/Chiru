"""
Self-bot related stuff.
"""
from discord.ext import commands

from bot import Chiru


class SelfBot(object):
    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True, names="93591378994397184")
    async def _93591378994397184(self, ctx):
        with open("selfbot/93591378994397184.png", 'rb') as f:
            await self.bot.send_file(ctx.channel, f, filename="u200b.png")


def setup(bot: Chiru):
    bot.add_cog(SelfBot(bot))