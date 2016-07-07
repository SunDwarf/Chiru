"""
Shell cog.
"""
import asyncio
import discord
from discord.ext import commands
from logbook import Logger

from bot import Chiru
from chiru.cogs.shell.docker import DockerInterface
from override import Context


class Shell(object):
    def __init__(self, bot: Chiru):
        self.bot = bot

        self.logger = Logger("Chiru::Shell")

        self.sessions = {}

    @commands.command(pass_context=True)
    async def shell(self, ctx: Context):
        """
        Invoke a new shell for your user.

        This will open an interactive Bash shell for you to use.
        """
        # Check if an active session isn't already open.
        if ctx.author.id in self.sessions:
            channel = self.sessions.get(ctx.author.id)[1]
            await self.bot.say("You already have an active session in {channel.name}.".format(channel=channel))
            return

        # Create the new interface, and open a new shell.
        await self.bot.say("Provisioning your shell...")
        interface = DockerInterface(ctx.author.id)
        subprocess = await interface.create_shell()

        self.sessions[ctx.author.id] = (interface, ctx.channel)
        await self.bot.say("Type \`\`exit to exit, or \`command to send a command to the shell.")

        # Enter the infinite loop.
        while True:
            def _check_msg(message: discord.Message):
                return message.content.startswith("`")

            new_message = await self.bot.wait_for_message(author=ctx.author, channel=ctx.channel, check=_check_msg)
            if new_message.content == "``exit":
                await self.bot.say("Okay, terminating your shell.")
                # Remove from sessions.
                del self.sessions[ctx.author.id]
                # Shutdown the container.
                # Send sigint.
                subprocess.send_signal(2)
                # Send an EOF to the container.
                subprocess.stdin.write_eof()
                # Wait for it to finish.
                try:
                    await asyncio.wait_for(subprocess.communicate(), 5)
                except asyncio.TimeoutError:
                    subprocess.kill()
                # Exit the loop.
                break

            new_content = new_message.content[1:]
            to_feed = new_content + "\n"

            # Feed it into stdin.
            subprocess.stdin.write(to_feed.encode())
            # subprocess.stdin.write_eof()
            try:
                stdout = await asyncio.wait_for(subprocess.stdout.read(2048), 0.2)
            except asyncio.TimeoutError:
                # Check if it's still alive.
                try:
                    await asyncio.wait_for(subprocess.wait(), 0.2)
                except asyncio.TimeoutError:
                    await self.bot.say("Warning: no stdout produced in time")
                    continue
                else:
                    await self.bot.say("Warning: shell died - respawning")
                    continue
            stdout = stdout.decode()
            if len(stdout) > 1900:
                lines = [stdout[i:i + 1900] for i in range(0, len(stdout), 1900)]
                for line in lines:
                    await self.bot.say("```{}```".format(line))
                continue

            await self.bot.say("```{}```".format(stdout))


def setup(bot: Chiru):
    bot.add_cog(Shell(bot))
