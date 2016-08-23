"""
Cog used for my server.
"""
import random

import datetime
import discord
import time
from discord.ext import commands

from bot import Chiru
from chiru import checks
from override import Context


class Fuyu:
    """
    Utilities for my server.
    """

    ABUSE_ROLE_ID = "217264202174169088"

    def __init__(self, bot: Chiru):
        self.bot = bot

    def __check(self, ctx: Context):
        return ctx.server.id == "198101180180594688"

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


def setup(bot: Chiru):
    bot.add_cog(Fuyu(bot))
