"""
Role-based feeds.
"""
import aioredis
import discord
from discord.ext import commands

from bot import Chiru
from override import Context


class Feeds:
    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def feeds(self, ctx: Context):
        """
        Shows the list of feeds that the channel has.

        A feed is something that users can opt-in to
        to receive news about a certain feed by running
        the `sub` command (and opt-out by doing the `unsub` command).
        You can publish to a feed by using the `publish` command.
        """

        keys = []

        # Gather a list of all the feeds for this channel.
        async with (await self.bot.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)

            # Scan keys.
            async for key in conn.iscan(match="cfg:{}:feeds:*".format(ctx.server.id)):
                keys.append(key.decode().split(":")[-1])

        # Format this nicely.
        formatted = "Feeds for this server:\n {}"
        if len(keys) < 1:
            fmt = formatted.format("\n**No feeds found for this server.**")

        else:
            fmt = formatted.format("")
            for key in keys:
                fmt += "\n - **{}**".format(key)

        await self.bot.say(fmt)

    @feeds.command(pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def create(self, ctx: Context, *, name: str):
        """
        Creates a new feed.
        """
        role = await self.bot.get_config(ctx.server, "feeds:{}".format(name))
        if role is not None:
            await self.bot.say("This role already exists.")
            return

        # Make a new role for the feed.
        role = await self.bot.create_role(ctx.server, name=name, permissions=discord.Permissions(0))

        # Set the role ID in the database.
        await self.bot.set_config(ctx.server, "feeds:{}".format(name), role.id)
        await self.bot.say("Created new feed role `{}`.".format(name))

    @feeds.command(pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: Context, *, name: str):
        """
        Removes a feed.
        """
        role = await self.bot.get_config(ctx.server, "feeds:{}".format(name))
        if role is None:
            await self.bot.say("This feed does not exist.")
            return

        role = discord.utils.get(ctx.server.roles, id=role)
        if role:
            await self.bot.delete_role(ctx.server, role)

        await self.bot.delete_config(ctx.server, "feeds:{}".format(name))
        await self.bot.say("Deleted feed role.")

    @commands.command(pass_context=True)
    async def sub(self, ctx: Context, *, name: str):
        """
        Subscribes to a feed.
        """
        role = await self.bot.get_config(ctx.server, "feeds:{}".format(name))
        if role is None:
            await self.bot.say("This feed does not exist.")
            return

        role = discord.utils.get(ctx.server.roles, id=role)
        if not role:
            await self.bot.say("This feed role has been deleted.")
            return

        await self.bot.add_roles(ctx.author, role)
        await self.bot.say("☑")

    @commands.command(pass_context=True)
    async def unsub(self, ctx: Context, *, name: str):
        """
        Unsubscribes from a feed.
        """
        role = await self.bot.get_config(ctx.server, "feeds:{}".format(name))
        if role is None:
            await self.bot.say("This feed does not exist.")
            return

        role = discord.utils.get(ctx.server.roles, id=role)
        if not role:
            await self.bot.say("This feed role has been deleted.")
            return

        await self.bot.remove_roles(ctx.author, role)
        await self.bot.say("☑")

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def publish(self, ctx: Context, name: str, *, content: str):
        """
        Publishes content to a feed.

        Everyone who is subscribed to the feed will be notified
        with the content.
        """
        role = await self.bot.get_config(ctx.server, "feeds:{}".format(name))
        if role is None:
            await self.bot.say("This feed does not exist.")
            return

        role = discord.utils.get(ctx.server.roles, id=role)
        if not role:
            await self.bot.say("This feed role has been deleted.")
            return

        await self.bot.delete_message(ctx.message)

        await self.bot.edit_role(ctx.server, role, mentionable=True)
        await self.bot.say("{}: {}".format(role.mention, content))
        await self.bot.edit_role(ctx.server, role, mentionable=False)


def setup(bot):
    bot.add_cog(Feeds(bot))
