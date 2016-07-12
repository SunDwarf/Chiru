"""
Fun commands.
"""
import functools

import aiohttp
import discord
import google
from discord.ext import commands
from io import BytesIO

from bot import Chiru
from chiru import util
from override import Context


class Fun(object):
    """
    aaa
    """

    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    async def stats(self, ctx: Context):
        """
        Show stats about the bot.
        """
        await self.bot.say(
            "Currently connected to `{}` servers, with `{}` channels and `{}` users.".format(
                len(self.bot.servers), len([x for x in self.bot.get_all_channels()]),
                len([x for x in self.bot.get_all_members()])
            )
        )

    @commands.command(pass_context=True)
    async def whois(self, ctx: Context, *, member: discord.Member):
        """
        Show detailed information about a user.
        """
        fmt = """WHOIS for user {m}:

```xl
Username: {member.name}#{member.discriminator}
Display name: {member.display_name}
User ID: {member.id}

Created: {cr}
Joined: {jr}

Colour: {member.colour}
Roles: {roles}

Avatar URL: <{member.avatar_url}>

Mutual servers: {mut}```"""
        await self.bot.say(fmt.format(m=str(member), member=member,
                                      cr=member.created_at, jr=member.joined_at,
                                      mut=self._calculate_mutual_servers(member),
                                      roles=', '.join(util.safe_roles(member.roles)))
                           )

    def _calculate_mutual_servers(self, member: discord.Member):
        # Calculates mutual servers.
        count = 0
        for serv in self.bot.servers:
            assert isinstance(serv, discord.Server)
            if serv.get_member(member.id):
                count += 1
        return count

    def _search_google(self, fn, query):
        """
        Callback for searching google.

        Used inside an executor.
        """
        search = fn(query)
        # Get the first item off of the search.
        result = next(search)
        return result

    @commands.group(pass_context=True, invoke_without_command=True)
    async def search(self, ctx: Context, *, searchstr: str):
        """
        Searches the web for something.

        Use `search images` for google images search.
        """
        result = await self.bot.loop.run_in_executor(
            None, functools.partial(self._search_google, google.search, searchstr)
        )
        await self.bot.say(result)

    @search.command(pass_context=True)
    async def images(self, ctx: Context, *, searchstr: str):
        """
        Search google images.
        """
        result = await self.bot.loop.run_in_executor(
            None, functools.partial(self._search_google, google.search_images, searchstr)
        )
        await self.bot.say(result)

    @commands.command(pass_context=True)
    async def info(self, ctx: Context):
        """
        Show information about the bot.
        """
        await self.bot.say("I'm {} - yet another bot.\n"
                           "I was written by Fuyu, the best programmer in the world.\n"
                           "Join my test server: https://discord.gg/Rh6jAXa".format(self.bot.user.name))

    @commands.command(pass_context=True, )
    async def upscale(self, ctx: Context, *, url: str):
        """
        Upscales an image using waifu2x.

        This takes a link to an image, and returns a link to the upscaled image.
        """
        sess = aiohttp.ClientSession()
        await self.bot.say(":hourglass: Upscaling image...")

        params = {
            "url": url,
            "scale": "2",  # yikes
            "noise": "-1",
            "style": "art"
        }

        async with sess.post("http://waifu2x.udp.jp/api", data=params) as r:
            assert isinstance(r, aiohttp.ClientResponse)
            if r.status != 200:
                await self.bot.say("Waifu2x returned an error - cannot upscale.")
                return
            file_content = await r.read()

        await self.bot.send_file(ctx.channel, BytesIO(file_content), filename="upscaled.png")

        sess.close()

def setup(bot: Chiru):
    bot.add_cog(Fun(bot))
