"""
Graylog-based logger.

Can also be used to search stuff, etc.
"""
import asyncio
import collections
import json

import logbook
from discord.ext import commands

from bot import Chiru
from chiru import checks
from override import Context


class Logger:
    def __init__(self, bot: Chiru):
        self.bot = bot

        self._reader = None
        self._writer = None

        self.counter = collections.Counter()

        self.logger = logbook.Logger("Chiru::Logging")
        self.logger.level = logbook.INFO

    async def _connect(self):
        """
        Connects the bot to Graylog.
        """
        cfg = self.bot.config["graylog"]
        ip = cfg["ip"]
        port = cfg.get("port") or 4545

        self._reader, self._writer = await asyncio.open_connection(host=ip, port=port)

    @property
    async def reader(self) -> asyncio.StreamReader:
        """
        Get the reader for Graylog.
        """
        if self._reader is None:
            await self._connect()
        return self._reader

    @property
    async def writer(self) -> asyncio.StreamWriter:
        if self._writer is None:
            await self._connect()
        return self._writer

    async def on_socket_response(self, data: dict):
        """
        Send the data to graylog.
        """
        writer = await self.writer

        # Get the event
        event = data['t']

        if event in ['GUILD_SYNC', 'MESSAGE_ACK']:
            self.logger.warning("Ignoring self-bot only messages...")
            return

        # Extract the `d` packet out.
        ndata = data.get('d')
        if not ndata:
            self.logger.warning("Recieved empty data: Event => {} Data => {}".format(event, data))
            return

        self.counter[event] += 1

        # Set the event field.
        ndata['event'] = event

        # Do some minor re-mapping to make the data cleaner.
        # Move the `author` attribute to the `user` attribute.
        # This is consistent with everything else.
        if 'author' in data:
            ndata['user'] = ndata['author']
            del ndata['author']

        if 'MESSAGE' in event:
            # Remap the message data.
            msg_data = {
                "id": ndata["id"],
            }
            if event != "MESSAGE_DELETE":
                msg_data["content"] = ndata["content"]
                msg_data["tts"] = ndata["tts"]
                msg_data["type"] = ndata["type"]

                del ndata["content"], ndata["tts"], ndata["type"]
            del ndata["id"]
            ndata["message"] = msg_data

        self.logger.debug("Recieved data: Event => {} OP => {}".format(event, data['op']))

        # Dump the JSON, and create a new message with a newline terminator.
        try:
            js = json.dumps(ndata)
        except TypeError:
            self.logger.error("Failed to serialize data: Data => {}".format(data))
            return

        dd = js.encode() + b"\n"

        writer.write(dd)

    @commands.group(pass_context=True)
    async def logging(self, ctx: Context):
        """
        Base logging command.

        This command does nothing by itself, and is just used as a group container.
        """

    @logging.command(pass_context=True)
    @commands.check(checks.is_owner)
    async def loglevel(self, ctx: Context, *, loglevel: str):
        """
        Changes the log level of the logger.
        """
        loglevel = getattr(logbook, loglevel.upper(), logbook.INFO)
        self.logger.level = loglevel
        await self.bot.say("Changed log level to {}.".format(loglevel))

    @logging.command(pass_context=True)
    async def events(self, ctx: Context):
        """
        Show the counter of events.
        """
        total = sum(self.counter.values())
        await self.bot.say("I have recieved {} events since startup.".format(total))
        await self.bot.say(repr(self.counter))


def setup(bot: Chiru):
    bot.add_cog(Logger(bot))
