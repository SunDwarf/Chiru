from bot import Chiru
from .web import bp


def setup(bot: Chiru):
    # Register the blueprints.
    bot.register_blueprint(bp)
