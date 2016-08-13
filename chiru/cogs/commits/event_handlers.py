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
    _channel_db = await bot.db.get_channels_for_repo(repo)

    channels = [bot.get_channel(str(channel.id)) for channel in _channel_db]
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
    if len(r.form["commits"]) == 0:
        return
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
        fmt = "**{repo}:** **{sender[login]}** added label `{label}` to issue " \
              "**#{issue[number]} {issue[title]}**" \
            .format(repo=repo, issue=r.form["issue"],
                    label=r.form['label']['name'], sender=r.form["sender"])

    elif action == "assigned":
        fmt = "**{repo}:** **#{issue[number]} {issue[title]}** " \
              "was assigned to **{issue[assignee][login]}**" \
              "\n(<{issue[html_url]}>)".format(
            repo=repo, issue=r.form["issue"]
        )

    elif action == "unassigned":
        fmt = "**{repo}:** **#{issue[number]} {issue[title]}** " \
              "was unassigned from **{issue[assignee][login]}**" \
              "\n(<{issue[html_url]}>)".format(
            repo=repo, issue=r.form["issue"]
        )

    elif action == "unlabelled":
        fmt = "**{repo}:** **{sender[login]}** removed label `{label}` from issue " \
              "**#{issue[number]} {issue[title]}**" \
            .format(repo=repo, issue=r.form["issue"],
                    label=r.form['label']['name'], sender=r.form["sender"])

    elif action == "reopened":
        fmt = "**{repo}:** **{sender[login]}** re-opened issue " \
              "**#{issue[number]} {issue[title]}**\n(<{issue[html_url]}>)" \
            .format(repo=repo, issue=r.form["issue"], sender=r.form["sender"])

    else:
        return
        # fmt = "**{repo}:** Unknown issue event recieved: {event}".format(repo=repo, event=action)

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


async def commit_comment(bot: Chiru, r: Request):
    """
    Handles comments on commits.
    """
    repo = r.form["repository"]["full_name"]
    sender = r.form["sender"]
    comment = r.form["comment"]

    fmt = "**{repo}:** **{sender[login]}** commented on commit `{commit}`\n<{comment[html_url]}>".format(
        repo=repo, sender=sender, commit=comment["commit_id"][0:7], comment=comment
    )

    for channel in await load_channels(bot, repo):
        if not channel:
            continue

        await bot.send_message(channel, fmt)


async def fork(bot: Chiru, r: Request):
    repo = r.form["repository"]["full_name"]
    forkee = r.form["forkee"]

    fmt = "**{repo}:** **{forkee[owner][login]}** forked this repo to **{forkee[full_name]}**" \
          "\n(<{forkee[html_url]}>)".format(
        repo=repo, forkee=forkee
    )

    for channel in await load_channels(bot, repo):
        if not channel:
            continue

        await bot.send_message(channel, fmt)


async def pr(bot: Chiru, r: Request):
    # Pull requests
    repo = r.form["repository"]["full_name"]

    action = r.form["action"]

    if action == "opened" or action == "reopened":
        fmt = "**{repo}:** **{pull_request[user][login]}** wants to merge {pull_request[commits]} commit(s) " \
              "in pull request **#{pull_request[number]}** - **{pull_request[title]}**" \
              "\n(<{pull_request[html_url]}>)".format(
            repo=repo, pull_request=r.form["pull_request"]
        )

    elif action == "closed":
        fmt = "**{repo}:** **#{pull_request[number]}** - **{pull_request[title]}** was {status}.\n" \
              "(<{pull_request[html_url]}>)".format(
            repo=repo, pull_request=r.form["pull_request"],
            status="merged" if r.form["pull_request"]["merged"] else "closed"
        )

    elif action == "synchronize":
        fmt = "**{repo}**: **{sender}** updated pull request " \
              "**#{pull_request[number]}** - **{pull_request[title]}**" \
              "\n(<{pull_request[html_url]}>)".format(
            repo=repo, pull_request=r.form["pull_request"],
            sender=r.form["sender"]["login"]
        )

    elif action == "assigned":
        fmt = "**{repo}:** **#{pull_request[number]}** - **{pull_request[title]}** " \
              "was assigned to **{pull_request[assignee][login]}**" \
              "\n(<{pull_request[html_url]}>)".format(
            repo=repo, pull_request=r.form["pull_request"]
        )

    elif action == "unassigned":
        fmt = "**{repo}:** **#{pull_request[number]}** - **{pull_request[title]}** " \
              "was unassigned from **{pull_request[assignee][login]}**" \
              "\n(<{pull_request[html_url]}>)".format(
            repo=repo, pull_request=r.form["pull_request"]
        )

    elif action == "labeled":
        fmt = "**{repo}:** **{sender[login]}** added label `{label}` to pull request " \
              "**#{pull_request[number]}** - **{pull_request[title]}**" \
            .format(repo=repo, pull_request=r.form["pull_request"],
                    label=r.form['label']['name'], sender=r.form["sender"])

    elif action == "unlabeled":
        fmt = "**{repo}:** **{sender[login]}** removed label `{label}` from pull request " \
              "**#{pull_request[number]}** - **{pull_request[title]}**" \
            .format(repo=repo, pull_request=r.form["pull_request"],
                    label=r.form['label']['name'], sender=r.form["sender"])

    else:
        return

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
    "commit_comment": commit_comment,
    "fork": fork,
    "pull_request": pr
}
