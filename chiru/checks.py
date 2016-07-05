from override import Context


def is_owner(ctx: Context):
    return ctx.message.author.id == "141545699442425856"


def has_manage_messages(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_messages


def has_manage_server(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_server


def has_manage_channels(ctx: Context):
    return ctx.author.permissions_in(ctx.channel).manage_channels
