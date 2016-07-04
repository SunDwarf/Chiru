"""
Event handlers.
"""
import aioredis
import discord
from kyokai import Request

from bot import Chiru


async def load_channels(bot: Chiru, repo: str):
    """
    Load the channels to send the bot to.
    """
    async with (await bot.get_redis()).get() as conn:
        assert isinstance(conn, aioredis.Redis)
        ids = await conn.smembers("commit_{}".format(repo))

    channels = [bot.get_channel(id.decode()) for id in ids]
    return channels


async def ping(bot: Chiru, r: Request):
    """
    PING event.
    """
    repo = r.form["repository"]["full_name"]
    formatted = "**{}:** Recieved *PING*.\n***Your webhooks are set up correctly.***".format(repo)
    channels = await load_channels(bot, repo)
    for channel in channels:
        if not channel:
            # Channel doesn't exist any more - move on.
            continue
        assert isinstance(channel, discord.Channel)
        await bot.send_message(channel, formatted)


async def push(bot: Chiru, r: Request):
    """
    PUSH event.
    """
    repo = r.form["repository"]["full_name"]
    # not the prettiest format
    header = "**{}:** **{}** pushed *{}* commit{} to branch **{}**" \
        .format(repo, r.form["pusher"]["name"], len(r.form["commits"]), 's' if len(r.form["commits"]) != 1 else '',
                r.form["ref"].split("/")[-1])
    for commit in r.form["commits"]:
        fmt = "`{}` {} [{}]".format(commit["id"][0:7], commit["message"], commit["author"]["username"])
        header += "\n" + fmt

    header += "\n<{}>".format(r.form["compare"])

    channels = await load_channels(bot, repo)
    for channel in channels:
        if not channel:
            continue
        await bot.send_message(channel, header)


handlers = {
    "ping": ping,
    "push": push
}
