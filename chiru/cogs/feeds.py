import json
from discord.ext import commands
import asyncio
import discord
import datetime
import re
from collections import Counter

DISCORD_API_ID = '81384788765712384'
USER_BOTS_ROLE = '178558252869484544'


class Config:
    """The "database" object. Internally based on ``json``."""

    def __init__(self, name, **options):
        self.name = name
        self.object_hook = options.pop('object_hook', None)
        self.encoder = options.pop('encoder', None)
        self.loop = options.pop('loop', asyncio.get_event_loop())
        if options.pop('load_later', False):
            self.loop.create_task(self.load())
        else:
            self.load_from_file()

    def load_from_file(self):
        try:
            with open(self.name, 'r') as f:
                self._db = json.load(f, object_hook=self.object_hook)
        except FileNotFoundError:
            self._db = {}

    async def load(self):
        await self.loop.run_in_executor(None, self.load_from_file)

    def _dump(self):
        with open(self.name, 'w') as f:
            json.dump(self._db, f, ensure_ascii=True, cls=self.encoder)

    async def save(self):
        await self.loop.run_in_executor(None, self._dump)

    def get(self, key, *args):
        """Retrieves a config entry."""
        return self._db.get(key, *args)

    async def put(self, key, value, *args):
        """Edits a config entry."""
        self._db[key] = value
        await self.save()

    async def remove(self, key):
        """Removes a config entry."""
        del self._db[key]
        await self.save()

    def __contains__(self, item):
        return self._db.__contains__(item)

    def __len__(self):
        return self._db.__len__()

    def all(self):
        return self._db


class API:
    """
    Feeds.

    Shamelessly copied from R.Danny.
    """

    def __init__(self, bot):
        self.bot = bot
        # channel_id to dict with <name> to <role id> mapping
        self.feeds = Config('feeds.json')

    @commands.group(name='feeds', pass_context=True, invoke_without_command=True)
    async def _feeds(self, ctx):
        """Shows the list of feeds that the channel has.

        A feed is something that users can opt-in to
        to receive news about a certain feed by running
        the `sub` command (and opt-out by doing the `unsub` command).
        You can publish to a feed by using the `publish` command.
        """
        server = ctx.server
        feeds = self.feeds.get(server.id, {})
        if len(feeds) == 0:
            await self.bot.say('This channel has no feeds.')
            return

        fmt = 'Found {} feeds.\n{}'
        await self.bot.say(fmt.format(len(feeds), '\n'.join('- ' + r for r in feeds)))

    @_feeds.command(name='create', pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def feeds_create(self, ctx, *, name: str):
        """Creates a feed with the specified name.

        You need Manage Roles permissions to create a feed.
        """
        channel = ctx.message.channel
        server = channel.server
        feeds = self.feeds.get(server.id, {})
        name = name.lower()
        if name in feeds:
            await self.bot.say('This feed already exists.')
            return

        # create the default role
        role_name = ctx.channel.name.replace(" ", "_").lower() + ' ' + name
        role = await self.bot.create_role(server, name=role_name, permissions=discord.Permissions.none())
        feeds[name] = role.id
        await self.feeds.put(server.id, feeds)
        await self.bot.say('\u2705')

    @_feeds.command(name='delete', aliases=['remove'], pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def feeds_delete(self, ctx, *, feed: str):
        """Removes a feed from the channel.

        This will also delete the associated role so this
        action is irreversible.
        """
        channel = ctx.message.channel
        server = channel.server
        feeds = self.feeds.get(server.id, {})
        feed = feed.lower()
        if feed not in feeds:
            await self.bot.say('This feed does not exist.')
            return

        role = feeds.pop(feed)
        try:
            await self.bot.delete_role(server, discord.Object(id=role))
        except discord.HTTPException:
            await self.bot.say('\U0001F52B')
        else:
            await self.feeds.put(server.id, feeds)
            await self.bot.say('\U0001F6AE')

    async def do_subscription(self, ctx, feed, action):
        channel = ctx.message.channel
        member = ctx.message.author
        server = ctx.server
        feeds = self.feeds.get(server.id, {})
        feed = feed.lower()

        if feed not in feeds:
            await self.bot.say('This feed does not exist.')
            return

        role = feeds[feed]
        function = getattr(self.bot, action)
        try:
            await function(member, discord.Object(id=role))
        except discord.HTTPException:
            # muh rate limit
            await asyncio.sleep(10)
            await function(member, discord.Object(id=role))
        else:
            await self.bot.send_message(channel, '\u2705')

    @commands.command(pass_context=True)
    async def sub(self, ctx, *, feed: str):
        """Subscribes to the publication of a feed.

        This will allow you to receive updates from the channel
        owner. To unsubscribe, see the `unsub` command.
        """
        await self.do_subscription(ctx, feed, 'add_roles')

    @commands.command(pass_context=True)
    async def unsub(self, ctx, *, feed: str):
        """Unsubscribe to the publication of a feed.

        This will remove you from notifications of a feed you
        are no longer interested in. You can always sub back by
        using the `sub` command.
        """
        await self.do_subscription(ctx, feed, 'remove_roles')

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def publish(self, ctx, feed: str, *, content: str):
        """Publishes content to a feed.

        Everyone who is subscribed to the feed will be notified
        with the content. Use this to notify people of important
        events or changes.
        """
        channel = ctx.message.channel
        server = channel.server
        feeds = self.feeds.get(server.id, {})
        feed = feed.lower()
        if feed not in feeds:
            await self.bot.say('This feed does not exist.')
            return

        role = discord.utils.get(server.roles, id=feeds[feed])
        if role is None:
            fmt = 'Uh.. a fatal error occurred here. The role associated with ' \
                  'this feed has been removed or not found. ' \
                  'Please recreate the feed.'
            await self.bot.say(fmt)
            return

        # delete the message we used to invoke it
        await self.bot.delete_message(ctx.message)

        # make the role mentionable
        await self.bot.edit_role(server, role, mentionable=True)

        # then send the message..
        msg = '{0.mention}: {1}'.format(role, content)[:2000]
        await self.bot.say(msg)

        # then make the role unmentionable
        await self.bot.edit_role(server, role, mentionable=False)


def setup(bot):
    bot.add_cog(API(bot))
