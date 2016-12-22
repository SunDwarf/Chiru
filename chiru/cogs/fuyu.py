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
    return ctx.server.id in ["198101180180594688"]


class Fuyu:
    """
    Utilities for my server.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    async def on_member_join(self, member: discord.Member):
        if member.server.id != "198101180180594688":
            return

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
    async def servername(self, ctx: Context, *, name: str):
        """
        Changes the name of my server.
        """
        await self.bot.edit_server(ctx.message.server, name=name)
        await self.bot.say(":heavy_check_mark: Changed server name.")

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
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2946.0 Safari/537.36",
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
