"""
Self-bot related stuff.
"""
import asyncio
import os

import aiohttp
import discord
import random

import time
from discord.ext import commands

from bot import Chiru
from chiru import util
from override import Context


class SelfBot(object):
    def __init__(self, bot: Chiru):
        self.bot = bot

        self._dont_mention_me = True

        self._last_mention = 0

    async def on_message(self, message: discord.Message):
        if self._dont_mention_me is False:
            return

        if not message.server or message.server.id != "175856762677624832":
            return

        if message.author.id == "174701939580207105":
            return

        if message.server.me.mention in message.content:
            if self._last_mention > time.time() - 5:
                return
            self._last_mention = time.time()
            await self.bot.send_message(message.channel, "Why do you feel the need to do this")

    @commands.command()
    async def dontfuckingmentionme(self):
        self._dont_mention_me = not self._dont_mention_me
        if self._dont_mention_me:
            msg = "DoNTFucKingMEntIonmE"
        else:
            msg = "FUckIngMEntIonMe"

        await self.bot.say(msg)

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
