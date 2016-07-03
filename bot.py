"""
Bot file.
"""
import sys

import discord
import logbook
import logging

import traceback
from discord.ext.commands import Bot, CommandError, CommandNotFound
from discord.ext.commands.view import StringView

from logbook.compat import redirect_logging
from logbook import StreamHandler

from override import Context

# Define logging stuff.
redirect_logging()

StreamHandler(sys.stderr).push_application()

initial_extensions = [
    'cogs.fun',
    'cogs.owner'
]
logging.root.setLevel(logging.INFO)


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

    async def on_ready(self):
        self.logger.info("Loaded Chiru, logged in as `{}`.".format(self.user.name))
        for cog in initial_extensions:
            try:
                self.load_extension(cog)
            except Exception as e:
                self.logger.critical("Could not load extension `{}`".format(cog, e))
                self.logger.exception()
            else:
                self.logger.info("Loaded extension {}.".format(cog))

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
            # No DMs
            await self.send_message(message.channel, "I don't accept private messages.")
            return

        # Process commands
        try:
            await self.process_commands(message)
        except Exception as e:
            lines = traceback.format_exception(type(e), e.__cause__, e.__cause__.__traceback__)
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


if __name__ == "__main__":
    client = Chiru(command_prefix="domo arigato ", description="AAAA")

    client.run(sys.argv[1])
