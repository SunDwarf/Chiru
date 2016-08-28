"""
Cog used for my server.
"""
import json
import random

import datetime

import aiohttp
import discord
import time
from discord.ext import commands

from bot import Chiru
from chiru import checks
from override import Context

AUTHORIZATION_URL = "https://discordapp.com/api/v6/oauth2/authorize"


class Fuyu:
    """
    Utilities for my server.
    """

    ABUSE_ROLE_ID = "217264202174169088"

    def __init__(self, bot: Chiru):
        self.bot = bot

    def __check(self, ctx: Context):
        return ctx.server.id == "198101180180594688"

    async def on_member_join(self, member: discord.Member):
        if member.server.id != "198101180180594688":
            return

        if member.bot:
            role = discord.utils.get(member.server.roles, name="Bots")
            await self.bot.add_roles(member, role)

    @commands.command(pass_context=True)
    @commands.check(checks.is_owner)
    async def abuselottery(self, ctx: Context, *roles: discord.Role):
        """
        Defines who gets to win the daily abuse lottery.
        """
        members = []
        for member in ctx.server.members:
            if any(r in member.roles for r in roles):
                members.append(member)

        await self.bot.say("Picking a new abuser...")
        chosen = random.choice(members)
        role = discord.utils.get(ctx.server.roles, id=self.ABUSE_ROLE_ID)

        await self.bot.add_roles(chosen, role)
        await self.bot.say("{} has got the abuse role! Hooray!".format(chosen.mention))

    @commands.command(pass_context=True)
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
                await self.bot.say("\N{NO ENTRY SIGN} Failed to add bot to server! Error `{}`".format(status))
            else:
                await self.bot.say("\N{THUMBS UP SIGN} Added new bot.")


def setup(bot: Chiru):
    bot.add_cog(Fuyu(bot))
