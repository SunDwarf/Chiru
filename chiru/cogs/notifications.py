"""
Notifications cog.
"""
import discord
from discord.ext import commands

from bot import Chiru
from chiru import checks
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
    @commands.check(checks.has_manage_server)
    async def all(self, ctx: Context):
        """
        Turn all notifications on.
        """
        await ctx.set_config("notifications", "all")
        await self.bot.say("Notifications turned on.")

    @notifications.command(pass_context=True)
    @commands.check(checks.has_manage_server)
    async def off(self, ctx: Context):
        """
        Turn all notifications off.
        """
        await ctx.set_config("notifications", "off")
        await self.bot.say("Notifications turned off.")

    @notifications.command(pass_context=True)
    @commands.check(checks.has_manage_server)
    async def bans(self, ctx: Context):
        """
        Only notify on bans.
        """
        await ctx.set_config("notifications", "bans")
        await self.bot.say("Notifications set to bans only.")

    @notifications.command(pass_context=True)
    @commands.check(checks.has_manage_server)
    async def joins(self, ctx: Context):
        """
        Only notify on joins.
        """
        await ctx.set_config("notifications", "joins")
        await self.bot.say("Notifications set to joins only.")

    async def on_member_join(self, member: discord.Member):
        if (await self.bot.get_config(member.server, "notifications")) in ["all", "joins"]:
            await self.bot.send_message(member.server.default_channel, "**{}** has joined!".format(member.name))

    async def on_member_ban(self, member: discord.Member):
        if (await self.bot.get_config(member.server, "notifications")) == ["all", "bans"]:
            await self.bot.send_message(member.server.default_channel, "**{}** got bent".format(member.name))

    async def on_member_unban(self, server: discord.Server, user: discord.User):
        if (await self.bot.get_config(server, "notifications")) == ["all", "bans"]:
            await self.bot.send_message(server.default_channel, "**{}** got unbanned.".format(user.name))

    async def on_member_remove(self, member: discord.Member):
        if (await self.bot.get_config(member.server, "notifications")) == ["all", "joins"]:
            await self.bot.send_message(member.server.default_channel, "**{}** left".format(member.name))


def setup(bot: Chiru):
    bot.add_cog(Notifications(bot))
