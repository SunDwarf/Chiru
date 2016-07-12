"""
Owner-only commands.
"""

import discord
import traceback
from discord.ext import commands
from discord.ext.commands import Context

from bot import Chiru
from chiru import util
from chiru.checks import is_owner


class Owner:
    def __init__(self, bot: Chiru):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def geninvite(self, ctx: Context, *, id: str):
        """
        Generate an instant invite to a server, using the ID.
        """
        chan = self.bot.get_channel(id)
        inv = await self.bot.create_invite(chan)
        assert isinstance(inv, discord.Invite)
        await self.bot.say(inv.url)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def game(self, ctx, *, game: str):
        """
        Change the game.
        """
        if "twitch.tv" not in game:
            game = discord.Game(name=game, type=0)
        else:
            game = discord.Game(url=game, type=1)

        await self.bot.change_status(game)

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def name(self, ctx, *, name: str):
        """
        Change the bot name.
        """
        await self.bot.edit_profile(username=name)
        await self.bot.say(":heavy_check_mark: Changed name to {}.".format(name))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def avatar(self, ctx, *, url: str):
        """
        Change the bot's avatar.
        """
        avatar = await util.get_file(url)
        await self.bot.edit_profile(avatar=avatar)
        await self.bot.say(":heavy_check_mark: Changed avatar.")

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def load(self, ctx, *, extension: str):
        """
        Load an extension.
        """
        try:
            self.bot.load_extension("chiru.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await self.bot.say("Could not load `{}` -> `{}`".format(extension, e))
        else:
            await self.bot.say("Loaded cog `chiru.cogs.{}`.".format(extension))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def unload(self, ctx, *, extension: str):
        """
        Unload an extension.
        """
        try:
            self.bot.unload_extension("chiru.cogs.{}".format(extension))
        except Exception as e:
            traceback.print_exc()
            await self.bot.say("Could not unload `{}` -> `{}`".format(extension, e))
        else:
            await self.bot.say("Unloaded `{}`.".format(extension))

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def reloadall(self, ctx):
        """
        Reload all extensions.
        """
        for extension in self.bot.extensions:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)

        await self.bot.say("Reloaded all.")

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def die(self, ctx):
        import ctypes
        ctypes.string_at(1)

    @commands.command(pass_context=True)
    @commands.check(is_owner)
    async def debug(self, ctx, *, command: str):
        """
        Run a debug command.
        """
        result = eval(command)
        await self.bot.say("`{}`".format(result))


def setup(bot: Chiru):
    bot.add_cog(Owner(bot))
