"""
Notifications cog.
"""
import discord
from discord.ext import commands

from bot import Chiru
from override import Context


class Notifications(object):
    """
    Notifications.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def notifications(self, ctx: Context):
        """
        Update join/leave/ban/kick/etc notification settings.
        """
        # Since this is the default command, just say the status.
        get = await ctx.get_config("notifications") or "off"
        await self.bot.say("Your server notifications status is **{}**.".format(get))

    @notifications.command(pass_context=True)
    async def on(self, ctx: Context):
        await ctx.set_config("notifications", "on")
        await self.bot.say("Notifications turned on.")

    @notifications.command(pass_context=True)
    async def off(self, ctx: Context):
        await ctx.set_config("notifications", "off")
        await self.bot.say("Notifications turned off.")

    async def on_member_join(self, member: discord.Member):
        if (await self.bot.get_config(member.server, "notifications")) == "on":
            await self.bot.send_message(member.server.default_channel, "**{}** has joined!".format(member.name))


def setup(bot: Chiru):
    bot.add_cog(Notifications(bot))
