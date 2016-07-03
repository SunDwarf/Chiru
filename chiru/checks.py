from discord.ext.commands import Context


def is_owner(ctx: Context):
    return ctx.message.author.id == "141545699442425856"