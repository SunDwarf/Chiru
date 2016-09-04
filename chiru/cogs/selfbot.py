"""
Self-bot related stuff.
"""
import asyncio
import discord
import random
from discord.ext import commands

from bot import Chiru
from chiru import util
from override import Context


class SelfBot(object):
    def __init__(self, bot: Chiru):
        self.bot = bot

    async def on_message(self, message: discord.Message):
        if not message.server or message.server.id != "175856762677624832":
            return

        if message.server.me.mention in message.content:
            if random.choice([0, 1, 2]) == 2:
                await self.bot.send_message(message.channel, "Please don't mention me.")

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

    @commands.command(pass_context=True)
    async def creepylog(self, ctx: Context):
        base_msg = await self.bot.say("creepy log bot!")
        while True:
            await self.bot.edit_message(base_msg, "Creepy log bot!")
            await asyncio.sleep(1)
            await self.bot.edit_message(base_msg, "Creepy Log Bot!")
            await asyncio.sleep(1)


def setup(bot: Chiru):
    bot.add_cog(SelfBot(bot))
