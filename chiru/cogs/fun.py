"""
Fun commands.
"""
import discord
from discord.ext import commands

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
        Show information about a user.
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


def setup(bot: Chiru):
    bot.add_cog(Fun(bot))
