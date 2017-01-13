from override import Context


def is_owner(ctx: Context):
    return ctx.message.author.id == "214796473689178133"


def has_manage_messages(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_messages


def has_manage_server(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_server


def has_manage_channels(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_channels


def is_whitelisted(ctx: Context):
    return ctx.server.id in ctx.bot.config.get("whitelisted_servers", [])
