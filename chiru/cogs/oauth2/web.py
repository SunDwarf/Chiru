"""
OAuth2 web data.
"""
import json

import discord
from itsdangerous import BadSignature
from kyoukai import Request
from kyoukai.blueprints import Blueprint
from kyoukai.context import HTTPRequestContext
from kyoukai.response import redirect
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from chiru.cogs.oauth2.flow import OAuth2Provider

bp = Blueprint("oauth2")


@bp.route("/oauth2/join")
async def oauth2_join_server(ctx: HTTPRequestContext):
    """
    Join the server specified by the config.
    """
    if ctx.request.cookies.get("KySess") is None:
        return redirect("/oauth2/login", 302)

    bot = ctx.request.extra["bot"]
    try:
        token_data = bot.http_signer.loads(ctx.request.cookies["KySess"].value)
    except BadSignature:
        return redirect("/oauth2/login", 302)

    flow = OAuth2Provider(bot)

    # Get the ID.
    s_data = bot.config["oauth2"].get("servers", {}).get(ctx.request.args.get("server", None))
    if not s_data:
        return json.dumps({"error": "server not found"}), 404, {"Content-Type": "application/json"}

    if s_data["type"] == "id":
        s_id = s_data["id"]
        serv = bot.get_server(s_id)
        if not serv:
            return json.dumps({"error": "bad server"}), 404, {"Content-Type": "application/json"}

        invites = await bot.invites_from(serv)
        if len(invites) == 0:
            try:
                invite = await bot.create_invite(serv)
            except discord.Forbidden:
                return json.dumps({"error": "bad server"}), 404, {"Content-Type": "application/json"}
        else:
            invite = invites[0]

    else:
        # Use the invite code.
        invite = s_data["code"]

    # Forcibly accept the invite.
    req = await flow.accept_invite(token_data, invite)

    if req.status_code == 401:
        return redirect("/oauth2/login", 302)

    return req.text, req.status_code, {"Content-Type": "application/json"}


@bp.route("/oauth2/server_list")
async def oauth2_server_info(ctx: HTTPRequestContext):
    if ctx.request.cookies.get("KySess") is None:
        return redirect("/oauth2/login", 302)

    bot = ctx.request.extra["bot"]
    try:
        token_data = bot.http_signer.loads(ctx.request.cookies["KySess"].value)
    except BadSignature:
        return redirect("/oauth2/login", 302)

    flow = OAuth2Provider(bot)
    server_data = await flow.get_server_data(token_data)

    if server_data.status_code == 401:
        return redirect("/oauth2/login", 302)

    return server_data.text, 200, {"Content-Type": "application/json"}


@bp.route("/oauth2/user_info")
async def oauth2_user_info(ctx: HTTPRequestContext):
    if ctx.request.cookies.get("KySess") is None:
        return redirect("/oauth2/login", 302)
    # Get user info using OAuth 2.
    bot = ctx.request.extra["bot"]
    try:
        token_data = bot.http_signer.loads(ctx.request.cookies["KySess"].value)
    except BadSignature:
        return redirect("/oauth2/login", 302)

    flow = OAuth2Provider(bot)
    user_data = await flow.get_user_data(token_data)

    if user_data.status_code == 401:
        return redirect("/oauth2/login", 302)

    return user_data.text, 200, {"Content-Type": "application/json"}


@bp.route("/oauth2/login")
async def oauth2_login(ctx: HTTPRequestContext):
    """
    Login with OAuth2.
    """
    scopes = ["identify", "guilds", "guilds.join"]
    flow = OAuth2Provider(ctx.request.extra["bot"])

    url = flow.get_auth_url(scopes)
    return redirect(url, 302)


@bp.route("/oauth2/authorize")
async def oauth2_authorize(ctx: HTTPRequestContext):
    """
    Authorize the bot at the same time.
    """
    scopes = ["identify", "guilds", "guilds.join", "bot"]
    flow = OAuth2Provider(ctx.request.extra["bot"])

    url = flow.get_auth_url(scopes)
    return redirect(url, 302)


@bp.route("/oauth2/redirect")
async def oauth2_redirect(ctx: HTTPRequestContext):
    assert isinstance(ctx.request, Request)
    code = ctx.request.args.get("code")
    if code is None:
        return json.dumps({"error": "no_code"}), 400, {"Content-Type": "application/json"}

    state = ctx.request.args.get("state")
    if state is None:
        return json.dumps({"error": "no_state"}), 400, {"Content-Type": "application/json"}

    bot = ctx.request.extra["bot"]

    flow = OAuth2Provider(bot)

    # Save the token.
    try:
        userid = await flow.save_first_token(state, code)
    except OAuth2Error as e:
        return e.json, 400, {"Content-Type": "application/json"}

    # Set the cookie.

    response = redirect("/", 302)
    response.cookies["KySess"] = bot.http_signer.dumps(userid)

    return response
