"""
Bot file.
"""
import os
import shutil
import sys

import aioredis as aioredis
import discord
import logbook
import logging
import yaml

import traceback

from discord.ext import commands
from discord.ext.commands import Bot, CommandError, CommandNotFound
from discord.ext.commands.view import StringView

from logbook.compat import redirect_logging
from logbook import StreamHandler

from override import Context

# Define logging stuff.
redirect_logging()

StreamHandler(sys.stderr).push_application()

initial_extensions = [
    'chiru.cogs.fun',
    'chiru.cogs.owner',
    'chiru.cogs.notifications',
    'chiru.cogs.commits'
]
logging.root.setLevel(logging.INFO)


def _get_command_prefix(bot: 'Chiru', message: discord.Message):
    if bot.config.get("dev"):
        return "domo arigato "
    else:
        return "chiru "


class Chiru(Bot):
    """
    Bot class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logbook.Logger("Chiru")
        self.logger.level = logbook.INFO

        # We still have to do this
        logging.root.setLevel(logging.INFO)

        try:
            cfg = sys.argv[1]
        except IndexError:
            cfg = "config.yml"

        if not os.path.exists(cfg):
            shutil.copy("config.example.yml", cfg)

        with open(cfg) as f:
            self.config = yaml.load(f)

        self._redis = None

    async def _connect_redis(self):
        """
        Connect to redis.
        """
        host = self.config.get("redis")["host"]
        port = self.config.get("redis")["port"]
        password = self.config.get("redis", {}).get("password")
        db = self.config.get("redis", {}).get("db", 0)
        self.logger.info("Connecting to redis://{}:{}/{}...".format(host, port, db))
        redis_pool = await aioredis.create_pool(
            (host, port),
            db=db, password=password
        )
        self._redis = redis_pool
        self.logger.info("Connected to redis.")

        return self._redis

    async def get_redis(self) -> aioredis.RedisPool:
        if self._redis is None:
            await self._connect_redis()

        return self._redis

    async def get_config(self, server: discord.Server, key: str):
        """
        Get a server config key.
        """
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            built = "cfg:{}:{}".format(server, key)
            x = await conn.get(built)
            if isinstance(x, bytes):
                return x.decode()
            return x

    async def get_key(self, key: str):
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            x = await conn.get(key)
            if isinstance(x, bytes):
                return x.decode()
            return x

    async def set_config(self, server: discord.Server, key: str, value, **kwargs):
        async with (await self.get_redis()).get() as conn:
            assert isinstance(conn, aioredis.Redis)
            built = "cfg:{}:{}".format(server, key)
            return await conn.set(built, value, **kwargs)

    async def on_ready(self):
        self.logger.info("Loaded Chiru, logged in as `{}`.".format(self.user.name))
        id = (await self.application_info()).id
        self.logger.info("Invite link: {}".format(discord.utils.oauth_url(id)))
        await self.get_redis()
        for cog in initial_extensions:
            try:
                self.load_extension(cog)
            except Exception as e:
                self.logger.critical("Could not load extension `{}`".format(cog, e))
                self.logger.exception()
            else:
                self.logger.info("Loaded extension {}.".format(cog))

    def __del__(self):
        self.loop.set_exception_handler(lambda *args, **kwargs: None)

    async def on_message(self, message):
        # Print logging output.

        if not isinstance(message.channel, discord.PrivateChannel):
            self.logger.info("Recieved message: {message.content} from {message.author.display_name}{bot}"
                             .format(message=message, bot=" [BOT]" if message.author.bot else ""))
            self.logger.info(" On channel: #{message.channel.name}".format(message=message))

        # Check for a valid server.
        if message.server is not None:
            self.logger.info(" On server: {} ({})".format(message.server.name, message.server.id))
        else:
            if not message.author.bot:
                # No DMs
                await self.send_message(message.channel, "I don't accept private messages.")
                return

        # Process commands
        try:
            await self.process_commands(message)
        except Exception as e:
            # Check the type of the error.
            if isinstance(e, (commands.errors.BadArgument, commands.errors.MissingRequiredArgument)):
                await self.send_message(message.channel, ":x: Bad argument: {}".format(' '.join(e.args)))
                return
            else:
                if isinstance(e, commands.errors.CommandInvokeError):
                    lines = traceback.format_exception(type(e), e.__cause__, e.__cause__.__traceback__)
                else:
                    lines = traceback.format_exception(type(e), e, e.__traceback__)
                await self.send_message(message.channel, "```py\n{}\n```".format(''.join(lines)))

    async def process_commands(self, message):
        """
        Override of process_commands to use our own context.
        """
        _internal_channel = message.channel
        _internal_author = message.author

        view = StringView(message.content)
        if self._skip_check(message.author, self.user):
            return

        prefix = self._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
            'prefix': invoked_prefix
        }
        ctx = Context(**tmp)
        del tmp

        if invoker in self.commands:
            command = self.commands[invoker]
            self.dispatch('command', command, ctx)
            await command.invoke(ctx)
            self.dispatch('command_completion', command, ctx)
        elif invoker:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)

    def main(self):
        self.run(self.config["oauth2_token"])


if __name__ == "__main__":
    client = Chiru(command_prefix=_get_command_prefix, description="AAAA")
    client.main()
