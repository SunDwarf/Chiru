"""
Self-bot related stuff.
"""
import discord
from discord.ext import commands

from bot import Chiru
from chiru import util
from override import Context


class SelfBot(object):
    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True, names=["93591378994397184"])
    async def _93591378994397184(self, ctx):
        with open("selfbot/93591378994397184.png", 'rb') as f:
            await self.bot.send_file(ctx.channel, f, filename="u200b.png")

    @commands.command(pass_context=True)
    async def beadick(self, ctx: Context):
        """
        Mention everyone in the channel without using @ everyone.
        """
        mentions = " ".join([member.mention for member in ctx.server.members])
        chunked = util.chunk(mentions)
        for chunk in chunked:
            await self.bot.say(chunk)

    @commands.command(pass_context=True)
    async def nukeinvs(self, ctx: Context):
        """
        Nukes the messages for a user.
        """
        count = 0
        async for message in self.bot.logs_from(ctx.channel):
            if 'discord.gg' in message.content:
                count += 1
                await self.bot.delete_message(message)

        await self.bot.say("Deleted {} messages".format(count))


def setup(bot: Chiru):
    bot.add_cog(SelfBot(bot))
