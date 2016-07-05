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


async def issues(bot: Chiru, r: Request):
    """
    Issues.
    """
    repo = r.form["repository"]["full_name"]
    action = r.form["action"]
    if action == "opened":
        fmt = "**{repo}:** **{issue[user][login]}** opened issue **#{issue[number]}**: " \
              "**{issue[title]}**\n(<{issue[html_url]}>)" \
            .format(repo=repo, issue=r.form["issue"])

    elif action == "created":  # what
        fmt = "**{repo}:** **{sender[login]}** " \
              "commented on issue **#{issue[number]} {issue[title]}**\n(<{issue[html_url]}>)" \
                .format(repo=repo, issue=r.form["issue"], sender=r.form["sender"])

    elif action == "closed":
        fmt = "**{repo}:** **{sender[login]}** closed issue **#{issue[number]} {issue[title]}**" \
              "\n(<{issue[html_url]}>)" \
                .format(repo=repo, issue=r.form["issue"], sender=r.form["sender"])

    elif action == "labeled":
        fmt = "**{repo}:** **{sender[login]}** added labels `{labels}` to issue " \
              "**#{issue[number]} {issue[title]}**" \
            .format(repo=repo, issue=r.form["issue"],
                    labels=' '.join("[" + l["name"] + "]" for l in r.form["issue"]["labels"]), sender=r.form["sender"])

    elif action == "reopened":
        fmt = "**{repo}:** **{sender[login]}** re-opened issue " \
              "**#{issue[number]} {issue[title]}**\n(<{issue[html_url]}>)" \
                .format(repo=repo, issue=r.form["issue"], sender=r.form["sender"])

    else:
        fmt = "**{repo}:** Unknown issue event recieved: {event}".format(repo=repo, event=action)

    for channel in await load_channels(bot, repo):
        if not channel:
            continue
        await bot.send_message(channel, fmt)

async def star(bot: Chiru, r: Request):
    """
    Star handler.
    """
    repo = r.form["repository"]["full_name"]
    sender = r.form["sender"]

    fmt = "**{repo}:** **{sender[login]}** starred this repo!".format(repo=repo, sender=sender)

    for channel in await load_channels(bot, repo):
        if not channel:
            continue

        await bot.send_message(channel, fmt)

handlers = {
    "ping": ping,
    "push": push,
    "issues": issues,
    "issue_comment": issues,
    "watch": star,
}
