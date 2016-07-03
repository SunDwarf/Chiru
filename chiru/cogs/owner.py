"""
Owner-only commands.
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context

from bot import Chiru
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


def setup(bot: Chiru):
    bot.add_cog(Owner(bot))
