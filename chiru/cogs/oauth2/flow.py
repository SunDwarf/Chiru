"""
Helpers for getting the flow.
"""
import asyncio
import functools

import json

import discord
from requests_oauthlib import OAuth2Session

from bot import Chiru

API_BASE_URL = "https://discordapp.com/api"
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

API_ME_URL = API_BASE_URL + '/users/@me'
API_GUILDS_URL = API_BASE_URL + '/users/@me/guilds'
API_INVITE_URL = API_BASE_URL + '/invite/{code}'


class OAuth2Provider(object):
    """
    Provider for OAuth2 stuff.
    """

    def __init__(self, bot: Chiru):
        self.bot = bot
        self.cfg = bot.config

    async def _coro_refresh_token(self, token: str):
        """
        Coroutine that refreshes the token.
        """
        await self.save_token(token)

    def _refresh_token(self, refreshed: str):
        # Callback to refresh the token.
        asyncio.run_coroutine_threadsafe(self._coro_refresh_token(refreshed), self.bot.loop)

    # Taken from Mee6 to create the sessions each time.
    def make_session(self, token = None, state = None, scope = None):
        return OAuth2Session(
            client_id=self.cfg["oauth2"]["client_id"],
            token=token,
            state=state,
            scope=scope,
            redirect_uri=self.cfg["oauth2"].get("redirect_url"),
            auto_refresh_kwargs={
                'client_id': self.cfg["oauth2"]["client_id"],
                'client_secret': self.cfg["oauth2"]["client_secret"],
            },
            auto_refresh_url=TOKEN_URL,
            token_updater=self._refresh_token
        )

    async def _get_saved_token(self, id: str) -> dict:
        """
        Get the saved token for the specified ID.
        """
        async with (await self.bot.get_redis()).get() as conn:
            token = await conn.get("token:{}".format(id))

        if token:
            token = token.decode()
            token = json.loads(token)

        return token

    def _get_user_data(self, token: dict):
        """Gets user data using requests."""

        session = self.make_session(token=token)
        req = session.get(API_ME_URL)
        return req

    async def get_user_data(self, id: str):
        """
        Get the user data using a User ID.
        """
        token = await self._get_saved_token(id)
        if not token:
            return None

        # Fetch the data.
        data = await self.get_user_data_token(token)
        return data

    async def get_user_data_token(self, token: dict):
        """
        Downloads user data using Oauth2.
        """
        f = functools.partial(self._get_user_data, token)
        return await self.bot.loop.run_in_executor(None, f)

    def _get_server_data(self, token: dict):
        """Gets server dating using requests."""
        session = self.make_session(token=token)
        req = session.get(API_GUILDS_URL)
        return req

    async def get_server_data_token(self, token: dict):
        f = functools.partial(self._get_server_data, token)
        return await self.bot.loop.run_in_executor(None, f)

    async def get_server_data(self, id: str):
        """
        Get server data using a User ID.
        """
        token = await self._get_saved_token(id)
        if not token:
            return None

        return await self.get_server_data_token(token)

    def _accept_invite(self, token, invite: discord.Invite):
        session = self.make_session(token=token)
        if isinstance(invite, discord.Invite):
            invite = invite.id

        # Post to the right URL.
        uri = API_INVITE_URL.format(code=invite)
        r = session.post(uri)
        return r

    async def accept_invite_token(self, token, invite: discord.Invite):
        """
        Accept an invite, using the token.
        """
        f = functools.partial(self._accept_invite, token, invite)
        return await self.bot.loop.run_in_executor(None, f)

    async def accept_invite(self, id: str, invite: discord.Invite):
        """
        Accept an invite on the user's behalf.
        """
        token = await self._get_saved_token(id)
        if not token:
            return None

        return await self.accept_invite_token(token, invite)

    def _get_user_token(self, state: str, code: str):
        session = self.make_session(state=state)
        discord_token = session.fetch_token(TOKEN_URL, client_secret=self.cfg["oauth2"]["client_secret"],
                                            code=code)
        return discord_token

    async def get_user_token(self, state: str, code: str):
        """
        Get the user token.
        """
        f = functools.partial(self._get_user_token, state, code)
        return await self.bot.loop.run_in_executor(None, f)

    def get_auth_url(self, scopes):
        """
        Get the authorization URL to log into Discord with.
        """
        session = self.make_session(scope=scopes)
        authorization_url, state = session.authorization_url(
            AUTHORIZATION_BASE_URL,
            access_type="offline"
        )
        return authorization_url

    async def save_first_token(self, state: str, code: str):
        """
        Saves the first token given to us by Discord in the DB.
        This returns the User ID.
        """
        token = await self.get_user_token(state, code)

        return (await self.save_token(token))[1]

    async def save_token(self, token: dict):
        """
        Saves the token to the redis DB, and returns it.
        """
        user_data = await self.get_user_data_token(token)
        user_id = user_data.json()["id"]
        # Set the token in the DB.
        key = "token:{}".format(user_id)

        data = json.dumps(token)

        async with (await self.bot.get_redis()).get() as conn:
            await conn.set(key.encode(), data)

        # Return the new token.
        return token, user_id
