"""
Voice.

Limited to certain servers.
"""
import collections

import asyncio
import functools

import discord
import time
import youtube_dl as youtube_dl
from discord.ext import commands

from bot import Chiru
from chiru import checks
from override import Context


def find_voice_channel(server: discord.Server, defaults=None):
    channels = ["chiru", "music"] + (defaults if isinstance(defaults, list) else [])
    # Search for a voice channel with the name specified in the config, and then Music/NavalBot as a fallback.
    for channel in server.channels:
        assert isinstance(channel, discord.Channel)
        if not channel.type == discord.ChannelType.voice:
            continue
        # Check the name.
        if channel.name.lower() in channels:
            chan = channel
            break
    else:
        return None
    return chan


class Voice(object):
    """
    Music class.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

        # Define the param stores.
        # It's like global variables, but class-local!
        self.queues = collections.defaultdict(lambda: asyncio.Queue())
        self.tasks = {}
        self.locks = collections.defaultdict(lambda: asyncio.Lock())
        self.curr_data = collections.defaultdict(lambda: dict())

    def get_lock(self, id) -> asyncio.Lock:
        return self.locks[id]

    def get_queue(self, id) -> asyncio.Queue:
        return self.queues[id]

    @commands.command("play", pass_context=True)
    @commands.check(checks.is_whitelisted)
    async def play(self, ctx: Context, *, url: str):
        """
        Enqueues a video.
        """
        # Get the lock, if it doesn't exist.
        lock = self.get_lock(ctx.server.id)

        # Get the queue.
        queue = self.get_queue(ctx.server.id)

        try:
            if lock.locked():
                await self.bot.say("Waiting for lock to clear.")
            await lock.acquire()
            chan = find_voice_channel(ctx.server)
            if not chan:
                await self.bot.say(":x: Could not find voice channel - Should be named `Music`.")
                return

            if not self.bot.is_voice_connected(ctx.message.server):
                try:
                    voice_client = await self.bot.join_voice_channel(channel=chan)
                except (discord.ClientException, asyncio.TimeoutError):
                    await self.bot.send(":x: Timeout of doom! Blame Discord.")
                    return
            else:
                voice_client = self.bot.voice_client_in(ctx.message.server)
        finally:
            lock.release()

        # Create a new youtube_dl.
        ydl = youtube_dl.YoutubeDL({
            "format": 'best', "ignoreerrors": True,
            "default_search": "ytsearch", "source_address": "0.0.0.0"
        })

        df = functools.partial(ydl.extract_info, url, download=False)
        try:
            if lock.locked():
                await self.bot.say(":warning: Waiting for another download to finish.")
            await lock.acquire()
            # Run the partial.
            await self.bot.say(":hourglass: Downloading video information...")
            info = await self.bot.loop.run_in_executor(None, df)
        except Exception as e:
            await self.bot.say(":no_entry: Something went wrong whilst downloading video information: `{}`.".format(e))
            return
        finally:
            lock.release()

        if not info:
            await self.bot.say(":no_entry: Could not download video information.")
            return

        # Switch based on if it is a playlist.
        if 'entries' in info:
            # Set the datas to the entries element of the info dict.
            datas = info['entries']
        else:
            # Set datas to to the info.
            datas = [info]

        # Loop over the entries, and add each to the queue.
        for entry in datas:
            # Add the data to the queue.
            # This goes in the form of:
            #  - context
            #  - downloaded entry
            await queue.put((ctx, entry))

        await self.bot.say(":heavy_check_mark: Added {} item(s) to the queue.".format(len(datas)))

        if ctx.server.id not in self.tasks:
            # Create a new task.
            t = self.bot.loop.create_task(self._iterate_queue(ctx))
            self.tasks[ctx.server.id] = t

    async def _play_item(self, ctx: Context, data: dict):
        """
        Actually plays the item.
        """
        wp_url = data.get("webpage_url")

        # Fuckken redownload the URL anyway.

        ydl = youtube_dl.YoutubeDL(
            {"format": 'webm[abr>0]/bestaudio/best', "ignoreerrors": True, "source_address": "0.0.0.0"})

        func = functools.partial(ydl.extract_info, wp_url, download=False)
        data = await self.bot.loop.run_in_executor(None, func)

        url = data.get("url")

        finished = asyncio.Event()

        # Create the new player.
        vc = self.bot.voice_client_in(ctx.server)
        if not vc:
            # WHAT
            raise IndentationError

        # Create a new ffmpeg player.
        player = vc.create_ffmpeg_player(url, after=lambda: self.bot.loop.call_soon_threadsafe(finished.set))

        player.start()
        await self.bot.send_message(ctx.channel, ":heavy_check_mark: Now playing: `{}`".format(data.get("title")))
        #await self.bot.say(":heavy_check_mark: Now playing: `{}`".format(data.get("title")))

        self.curr_data[ctx.server.id]["player"] = player
        self.curr_data[ctx.server.id]["curr_info"] = data
        self.curr_data[ctx.server.id]["start_time"] = time.time()
        self.curr_data[ctx.server.id]["voteskips"] = []

        # Wait for it to finish.
        await finished.wait()

        # Clear data.
        del self.curr_data[ctx.server.id]

    async def _iterate_queue(self, ctx):
        """
        Get some new data from the queue and play it.
        """
        while True:
            queue = self.queues[ctx.server.id]
            if not queue:
                return

            try:
                item = await queue.get()
            except Exception:
                self.bot.logger.exception()
                return

            # Await the play task.
            try:
                await self._play_item(*item)
            except IndentationError:
                return


def setup(bot: Chiru):
    bot.add_cog(Voice(bot))
