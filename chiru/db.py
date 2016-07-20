"""
Chiru's database handler.

Connects the bot to a postgresql database, which transparently threadpools everything to make it async.
"""
import discord
import random
import sqlalchemy as sa
import string
from asyncio_extras import threadpool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker, Session

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

    @property
    def session(self) -> Session:
        return self._session

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

    def __repr__(self):
        return "<ChiruDatabase connected to `{}`>".format(self.db_uri)

    __str__ = __repr__


association_table = sa.Table(
    'channel_link', Base.metadata,
    sa.Column('channel_id', sa.Integer, sa.ForeignKey('channel.id')),
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

    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))


class NicknameChange(Base):
    """
    Tracks nickname changes.
    """
    __tablename__ = "nickname_change"

    id = sa.Column(sa.Integer, primary_key=True)

    before = sa.Column(sa.String)
    after = sa.Column(sa.String)

    member_id = sa.Column(sa.Integer, sa.ForeignKey("member.id"))


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
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))

    # Track the server.
    server_id = sa.Column(sa.Integer, sa.ForeignKey("server.id"))

    # Track messages.
    messages = relationship("Message")


class Server(Base):
    """
    Represents a server.
    """
    __tablename__ = "server"

    # Did somebody say snowflakes?
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    name = sa.Column(sa.String)

    owner_id = sa.Column(sa.Integer, sa.ForeignKey("member.id"))
    owner = relationship("Member", backref="server")

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
    server_id = sa.Column(sa.Integer, sa.ForeignKey("server.id"))

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
    channel_id = sa.Column(sa.Integer, sa.ForeignKey("channel.id"))

    # Member link.
    member_id = sa.Column(sa.Integer, sa.ForeignKey("member.id"))


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
