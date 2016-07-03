"""
Overrides.
"""
import discord
from discord.ext import commands


class Context(commands.Context):
    """
    Overriden context.
    """
    def __init__(self, **attrs):
        self.bot = attrs.pop('bot', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.prefix = attrs.pop('prefix')
        self.command = attrs.pop('command', None)
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)

        self._message = attrs.pop('message', None)

    @property
    def message(self) -> discord.Message:
        return self._message

    @property
    def server(self) -> discord.Server:
        return self._message.server

    @property
    def channel(self) -> discord.Channel:
        return self._message.channel

    @property
    def author(self) -> discord.Member:
        return self._message.author
