"""
Utilities cog.
"""
import asyncio

import datetime
import discord
import time
from discord.ext import commands

from bot import Chiru
from override import Context


class Utilities:
    """
    Useful for tedious server things.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    async def joinedat(self, ctx: Context, *, target: discord.Member):
        """
        Shows when the user joined.
        """
        await self.bot.say("{} joined this server at: `{}`.".format(target.name, target.joined_at))

    @commands.group(pass_context=True)
    async def getperms(self, ctx: Context, *, number: int):
        """
        Gets the permissions of a permissions number.
        """
        perms = discord.Permissions(number)
        fmt = "```http\n"
        for name, perm in perms:
            fmt += "{}: {}\n".format(name.replace("_", " ").capitalize(), perm)

        fmt += "```"
        await self.bot.say(fmt)

    @commands.command(pass_context=True)
    async def getroleid(self, ctx: Context, *, role: discord.Role):
        """
        Gets the role ID associated with the role specified.
        """
        await self.bot.say("`{}`".format(role.id))

    @commands.command(pass_context=True)
    async def rolecount(self, ctx: Context, *, role: discord.Role):
        """
        Returns the number of people in a specified role.
        """
        counter = 0
        for member in ctx.server.members:
            if role in member.roles:
                counter += 1

        await self.bot.say("`{}`".format(counter))

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def resetnames(self, ctx: Context):
        """
        Resets the nicknames of all members on a server (if possible).
        """
        futures = []
        for member in ctx.server.members:
            if member.top_role.position < ctx.server.me.top_role.position:
                futures.append(self.bot.change_nickname(member, None))

        results = await asyncio.gather(*futures, return_exceptions=True)

        changed = sum(1 for _ in results if not isinstance(_, Exception))

        await self.bot.say("Changed `{}` nicknames.".format(changed))

    @commands.command(pass_context=True)
    async def uptime(self, ctx: Context):
        """
        Shows the bot's uptime.
        """
        uptime = time.time() - self.bot.start_time

        m, s = divmod(uptime, 60)
        h, m = divmod(m, 60)
        formatted = "%d:%02d:%02d" % (h, m, s)

        await self.bot.say("Bot has been running for `{}`.".format(formatted))

    @commands.command(pass_context=True)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx: Context):
        """
        Resets as many permissions as it can.

        This will effectively remove all permissions from all channels.
        It is recommended to deny Read Messages to @ everyone before doing this.
        """
        await self.bot.say("**THIS WILL WIPE A LARGE PORTION OF YOUR SERVER. ARE YOU 100% SURE? [y/N]**")
        msg = await self.bot.wait_for_message(timeout=5, author=ctx.author, channel=ctx.channel, content="y")

        if msg is None:
            await self.bot.say("OK, cancelling.")
            return

        # Nuke roles.
        for role in ctx.server.roles:
            try:
                await self.bot.delete_role(role.server, role)
            except Exception as e:
                self.bot.logger.error("Could not delete role: {}".format(e))
            else:
                self.bot.logger.info("Deleted role {}.".format(role.name))

        await self.bot.say("Nuked roles.")

        # Nuke channel overrides.
        for channel in ctx.server.channels:
            # Reset the default overwrite.
            assert isinstance(channel, discord.Channel)

            override = discord.PermissionOverwrite()
            try:
                await self.bot.edit_channel_permissions(channel, ctx.server.default_role, override)
            except Exception as e:
                self.bot.logger.error("Could not edit permissions: {}".format(e))
            else:
                self.bot.logger.info("Edited permissions in {}.".format(channel.name))

            for role in channel.changed_roles:
                try:
                    await self.bot.delete_channel_permissions(channel, role)
                except Exception as e:
                    self.bot.logger.error("Could not edit permissions: {}".format(e))
                else:
                    self.bot.logger.info("Edited permissions in {}.".format(channel.name))

            for member in ctx.server.members:
                overwrite = channel.overwrites_for(member)

                if not any([v[1] for v in overwrite]):
                    self.bot.logger.info("Skipping {}.".format(member))
                    continue

                try:
                    await self.bot.delete_channel_permissions(channel, member)
                except Exception as e:
                    self.bot.logger.error("Could not edit permissions: {}".format(e))
                else:
                    self.bot.logger.info("Edited permissions in {}.".format(channel.name))

        await self.bot.say("Nuked overrides.")


def setup(bot: Chiru):
    bot.add_cog(Utilities(bot))
