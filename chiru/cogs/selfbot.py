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
        """
        Don't fucking mention me.
        """
        if self._dont_mention_me is False:
            return

        if not message.server:
            return

        # Check if DontFuckingMentionMe is on on this server.
        if await self.bot.get_config(message.server, "nomentions") != "y":
            return

        # Check if they're in the whitelist.
        if message.author.id in await self.bot.get_set(message.server, "mention_whitelist"):
            return

        if message.server.me in message.mentions:
            if self._last_mention > time.time() - 2:
                return
            self._last_mention = time.time()
            await self.bot.send_message(message.channel, "{} Heck Off - Please don't mention me here".format(
                message.author.mention))

    @commands.group(pass_context=True, invoke_without_command=True)
    async def dontfuckingmentionme(self, ctx: Context):
        """
        Please, Don't Fucking Mention Me.
        """
        status = await self.bot.get_config(ctx.message.server, "nomentions")
        if status == "y":
            await self.bot.say("Mentions are NOT ALLOWED HECK OFF")
        else:
            await self.bot.say("Mentions are allowed.")

    @dontfuckingmentionme.command(pass_context=True)
    async def on(self, ctx: Context):
        """
        Turns anti-mention bot on.
        """
        await self.bot.set_config(ctx.message.server, "nomentions", "y")
        await self.bot.say("DonTFUcKIngMentIoNme")

    @dontfuckingmentionme.command(pass_context=True)
    async def wadd(self, ctx: Context, member: discord.Member):
        """
        Adds somebody to the mention whitelist.
        """
        await self.bot.add_to_set(ctx.server, "mention_whitelist", member.id)
        await self.bot.say("{} is :ok:".format(member.name))

    @dontfuckingmentionme.command(pass_context=True)
    async def wrem(self, ctx: Context, member: discord.Member):
        await self.bot.remove_from_set(ctx.server, "mention_whitelist", member.id)
        await self.bot.say("{} can Heck OFF".format(member.name))

    @dontfuckingmentionme.command(pass_context=True)
    async def off(self, ctx: Context):
        """
        Turns anti-mention bot off.
        """
        await self.bot.set_config(ctx.message.server, "nomentions", "n")
        await self.bot.say("MEntIonS Are OK!!!!")

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
