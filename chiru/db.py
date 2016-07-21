"""
Chiru's database handler.

Connects the bot to a postgresql database, which transparently threadpools everything to make it async.
"""
import datetime

import asyncio
import discord
import random

import logbook
import sqlalchemy as sa
import string
from asyncio_extras import threadpool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker, Session

import bot

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)


class ChiruDatabase:
    """
    Represents the state handler for the Chiru database engine.

    This is normally accessed via `bot.db`.
    """

    def __init__(self, uri):
        if uri is None:
            # AAAA
            return
        self.db_uri = uri

        self.engine = sa.create_engine(self.db_uri)
        self._session_maker = sessionmaker(bind=self.engine)

        self._session = self._session_maker()

        self._ready = asyncio.Event()

        self._write_queue = asyncio.Queue()

        self.logger = logbook.Logger("Chiru::Database")

    @property
    def session(self) -> Session:
        try:
            return self._session
        except AttributeError:
            raise Exception("Tried to run DB action on non-DB enabled bot")

    @threadpool
    def create_link(self, channel: discord.Channel, repo: str):
        """
        Create a link between a channel and a repository.

        This returns the Link object.
        """
        created = False
        channel_id = channel.id
        channel_name = channel.name

        channel = self.session.query(Channel).filter(Channel.id == int(channel_id)).first()
        if channel is None:
            # Create a new channel object.
            channel = Channel(id=channel_id, name=channel_name)

        # Create a new CommitLink.
        link = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if link is None:
            link = CommitLink(
                repo_name=repo,
                secret=''.join(
                    random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(16)
                )
            )
            created = True

        if channel not in link.channels:
            link.channels.append(channel)

        self.session.merge(channel)
        self.session.merge(link)
        self.session.commit()

        return link, created

    @threadpool
    def get_channels_for_repo(self, repo: str):
        """
        Used by the Commits module to get the channels for a repository.

        Automatically asyncified with the threadpool decorator.
        """
        repo = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if repo is None:
            return []
        channels = [c for c in repo.channels]

        return channels

    @threadpool
    def get_repos_for_channel(self, channel: discord.Channel):
        """
        Used by the Commits module to get the repositories associated with a channel.
        """
        channel = self.session.query(Channel).filter(Channel.id == channel.id).first()
        if channel is None:
            return []
        repos = [r for r in channel.links]

        return repos

    @threadpool
    def get_secret(self, repo: str):
        """
        Used by the commits module to get the secret of the specified repo.
        """
        repo = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if not repo:
            return None

        return repo.secret

    @threadpool
    def remove_link(self, channel: discord.Channel, repo: str):
        """
        Remove a channel link.
        """
        repo = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if repo is None:
            return False

        channel = self.session.query(Channel).filter(Channel.id == int(channel.id)).first()

        try:
            repo.channels.remove(channel)
            self.session.commit()
        except Exception:
            return False
        else:
            return True

    async def run_queues(self):
        """
        Turn on the database queue fetching.

        Inside Chiru's logger, most new things are written to the database. These writes are submitted inside a
        queue; the queue fetching comes from the main thread, but the writes are performed inside an executor.

        This prevents breaking everything due to async writes but it also prevents blocking the main thread with
        database writes.
        """
        # Wait until we're ready to write.
        await self._ready.wait()

        # Loop infinitely.
        while True:
            if not self._ready.is_set():
                # This allows pausing of the database queue whilst we're not ready to write.
                await self._ready.wait()

            # Get a new item off of the write queue.
            new_item = await self._write_queue.get()

            # self._write_item is a threadpool'd item.
            # We await that with the item to wait, which will switch appropriately.
            # Then we loop again.
            try:
                await self._write_item(new_item)
            except Exception:
                # Uh oh!
                self.logger.critical("Write failed!")
                self.logger.exception()

    @threadpool
    def _write_item(self, item: object):
        """
        Internal method for actually writing the items to the database.
        """
        # Switch based on type.
        if isinstance(item, discord.Message):
            # It's a message, so we do stuff with the message, like update the tables and stuff
            s_id = item.server.id
            server = self.session.query(Server).filter(Server.id == s_id).first()
            if not server:
                # why
                # Create a new server.
                server = Server(id=s_id, name=item.server.name)
                self.session.add(server)
            # Check if the message has already existed.
            msg = self.session.query(Message).filter(Message.id == item.id).first()
            if not msg:
                msg = Message(id=item.id, content=item.content,
                              deleted=False)
            # Get the Member, too.
            member = self._get_member(item.author)

    def _get_member(self, author: discord.Member):
        """
        Get the member and automatically add it and a user to the session if it doesn't exist.
        """
        member = self.session.query(Member).filter(Member.user_id == author.id).first()
        if member is None:
            # Get the user, or create it.
            user = self.session.query(User).filter(User.id == member.id).first()
            if user is None:
                user = User(id=author.id, created_at=author.created_at)
                # Create a new UsernameChange.
                u_c = UsernameChange(before=None, after=author.name)
                user.usernames.append(u_c)
                self.session.add(user)
            else:
                # Check the username.
                username_changes = self.session.query(UsernameChange) \
                    .filter(UsernameChange.user_id == author.id) \
                    .order_by(UsernameChange.changed_at.desc()).first()
                if not username_changes:
                    u_change = UsernameChange(before=None, after=author.name)
                else:
                    if author.name != username_changes.after:
                        u_change = UsernameChange(before=username_changes.after, after=author.name)
                    else:
                        u_change = None

                if u_change:
                    user.usernames.append(u_change)

            member = Member(joined_at=author.joined_at,
                            user=user)
            n_c = NicknameChange(before=None, after=author.nick)
            member.nicknames.append(n_c)

            member.user = user

            self.session.add(member)
        else:
            nickname_changes = self.session.query(NicknameChange) \
                        .filter(NicknameChange.member_id == member.id) \
                        .order_by(NicknameChange.changed_at.desc())


    async def populate_db(self, bot):
        """
        Actual coroutine because create_task doesn't like threadpool decorator.
        """
        await self._populate_db(bot)

    @threadpool
    def _populate_db(self, bot: bot.Chiru):
        """
        Populates the database.

        This can take several years.
        """
        # We only add servers and channels.
        # Everything else is populated
        # Add servers.
        for server in bot.servers:
            sobb = self.session.query(Server).filter(Server.id == server.id).first()
            if sobb is None:
                sobb = Server(id=server.id, name=server.name)
                self.session.add(sobb)
            else:
                if sobb.name != server.name:
                    sobb.name = server.name
                    self.session.add(sobb)

        # Add channels.
        for channel in bot.get_all_channels():
            cobb = self.session.query(Channel).filter(Channel.id == channel.id).first()
            if cobb is None:
                cobb = Channel(id=channel.id, name=channel.name)
                self.session.add(cobb)
            else:
                if cobb.name != channel.name:
                    cobb.name = channel.name
                    self.session.add(cobb)

        self.session.commit()

        bot.loop.call_soon_threadsafe(self._ready.set)

    def __repr__(self):
        return "<ChiruDatabase connected to `{}`>".format(self.db_uri)

    __str__ = __repr__


association_table = sa.Table(
    'channel_link', Base.metadata,
    sa.Column('channel_id', sa.BigInteger, sa.ForeignKey('channel.id')),
    sa.Column('link_id', sa.Integer, sa.ForeignKey('commit_link.id'))
)


class UsernameChange(Base):
    """
    Tracks username changes.
    """
    __tablename__ = "username_change"

    id = sa.Column(sa.Integer, primary_key=True)

    before = sa.Column(sa.String)
    after = sa.Column(sa.String)

    changed_at = sa.Column(sa.DateTime)

    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("user.id"))


class NicknameChange(Base):
    """
    Tracks nickname changes.
    """
    __tablename__ = "nickname_change"

    id = sa.Column(sa.Integer, primary_key=True)

    before = sa.Column(sa.String)
    after = sa.Column(sa.String)

    changed_at = sa.Column(sa.DateTime)

    member_id = sa.Column(sa.BigInteger, sa.ForeignKey("member.id"))


class User(Base):
    """
    Represents a User.
    """
    __tablename__ = "user"

    # Snowflake ID.
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    created_at = sa.Column(sa.DateTime)

    # Track username changes.
    usernames = relationship("UsernameChange", backref="user")

    # Track member instances.
    members = relationship("Member", backref="user")


class Member(Base):
    """
    Represents a Member object.

    This is a User w/ a server.

    Tracks member data changes, and such.
    """
    __tablename__ = "member"

    # Member ID != User ID.
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)

    joined_at = sa.Column(sa.DateTime)

    nicknames = relationship("NicknameChange", backref="member")

    # Track the user.
    user_id = sa.Column(sa.BigInteger, sa.ForeignKey("user.id"))

    # Track the server.
    server_id = sa.Column(sa.BigInteger, sa.ForeignKey("server.id"))

    # Track messages.
    messages = relationship("Message", backref="message")


class Server(Base):
    """
    Represents a server.
    """
    __tablename__ = "server"

    # Did somebody say snowflakes?
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    name = sa.Column(sa.String)

    channels = relationship("Channel", backref="server")


class Channel(Base):
    """
    Represents a channel in logging and links.
    """
    __tablename__ = "channel"

    # No autoincrementing ID - this is provided to us by Discord as the snowflake.
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    name = sa.Column(sa.String)

    messages = relationship("Message", backref="channel")

    # Track the server.
    server_id = sa.Column(sa.BigInteger, sa.ForeignKey("server.id"))

    links = relationship(
        "CommitLink",
        secondary=association_table,
        back_populates="channels")


class Message(Base):
    """
    Represents a message.
    """
    __tablename__ = "message"

    # MORE SNOWFLAKES
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    content = sa.Column(sa.String)

    deleted = sa.Column(sa.Boolean, default=False)

    # Channel link.
    channel_id = sa.Column(sa.BigInteger, sa.ForeignKey("channel.id"))

    # Member link.
    member_id = sa.Column(sa.BigInteger, sa.ForeignKey("member.id"))


class CommitLink(Base):
    """
    Represents links between a repository and a channel.
    """
    __tablename__ = "commit_link"
    # Autoincrement this PK, as the IDs aren't really meaningful.
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)

    # author/repo, rather than just the repository name.
    # this makes querying easier.
    repo_name = sa.Column(sa.String)

    # Secret, used for authenticating the connection.
    secret = sa.Column(sa.String)

    channels = relationship(
        "Channel",
        secondary=association_table,
        back_populates="links")
