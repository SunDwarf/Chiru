"""
Cog used for my server.
"""
import json
import random

import datetime

import aiohttp
import asyncio
import discord
import time
from discord.ext import commands

from bot import Chiru
from chiru import checks
from override import Context

AUTHORIZATION_URL = "https://discordapp.com/api/v6/oauth2/authorize"


def fuyu_check(ctx: Context):
    return ctx.server.id in ["198101180180594688", "169602212769562626"]


class Fuyu:
    """
    Utilities for my server.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    async def on_member_join(self, member: discord.Member):
        if member.server.id != "198101180180594688":
            return

        # Auto-nickname them.
        dt = datetime.datetime.now()
        if dt.month == 10:
            nickname = "spooky {}".format(member.name)
            await self.bot.change_nickname(member, nickname)
        elif dt.month in [11, 12]:
            nickname = "festive {}".format(member.name)
            await self.bot.change_nickname(member, nickname)

    async def on_message(self, message: discord.Message):
        if not isinstance(message.author, discord.Member):
            return

        if message.author.server.id != "198101180180594688":
            return

        if message.author.id == message.server.me.id:
            return

        if "triggered" in message.content:
            await self.bot.send_message(message.channel, "haha triggered xd")

    @commands.command(pass_context=True)
    @commands.check(fuyu_check)
    @commands.has_permissions(manage_server=True)
    async def massnick(self, ctx: Context, prefix: str, suffix: str=""):
        """
        Mass nicknames a server with the specified prefix.
        """
        coros = []

        for member in ctx.server.members:
            coros.append(self.bot.change_nickname(member, "{}{}{}".format(prefix, member.name, suffix)))

        fut = asyncio.gather(*coros, return_exceptions=True)

        while not fut.done():
            await self.bot.type()
            await asyncio.sleep(5)

        count = sum(1 for i in fut.result() if not isinstance(i, Exception))

        await self.bot.say("Changed `{}` nicks.".format(count))

    @commands.command(pass_context=True)
    @commands.check(fuyu_check)
    async def addbot(self, ctx: Context, client_id: int):
        """
        Adds a bot to my server.

        This requires your client ID.
        Your bot will be added with no permissions.
        """
        payload = {
            "guild_id": ctx.server.id,
            "authorize": True,
            "permissions": 0
        }

        headers = {
            "Authorization": self.bot.config.get("bot_add_token"),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36",
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as sess:
            response = await sess.post(AUTHORIZATION_URL,
                                       params={"client_id": client_id,
                                               "scope": "bot"},
                                       headers=headers,
                                       data=json.dumps(payload))
            assert isinstance(response, aiohttp.ClientResponse)
            status = response.status
            js = await response.json()
            if status != 200:
                await self.bot.say("\N{NO ENTRY SIGN} Failed to add bot to server! Error `{}`".format(js))
            else:
                if 'location' in js and 'invalid_request' in js['location']:
                    await self.bot.say("\N{NO ENTRY SIGN} Invalid client ID.")
                else:
                    await self.bot.say("\N{THUMBS UP SIGN} Added new bot.")


def setup(bot: Chiru):
    bot.add_cog(Fuyu(bot))
