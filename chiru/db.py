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

        self._session = self._session_maker()  # type: Session

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
    def cleanup_links(self):
        """
        Cleanup stale links.
        """
        repos = self.session.query(CommitLink).all()

        removed = []
        for repo in repos:
            # Less than 1 channel, so it's not linked anywhere.
            if len(repo.channels) < 1:
                self.session.delete(repo)
                removed.append(repo)

        for x in removed:
            self.logger.info("Removed repo {} as it has no commit links".format(x.repo_name))

        self.session.commit()

        return len(removed)

    @threadpool
    def remove_link(self, channel: discord.Channel, repo: str):
        """
        Remove a channel link.
        """
        repo = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if repo is None:
            return False

        channel = self.session.query(Channel).filter(Channel.id == int(channel.id)).first()
        print(channel, repo.channels, channel in repo.channels)

        if channel in repo.channels:
            repo.channels.remove(channel)
        else:
            return False

        # Check if the repo has no channels.
        if len(repo.channels) == 0:
            self.session.delete(repo)
        else:
            self.session.merge(repo)

        try:
            self.session.commit()
        except Exception:
            self.logger.error("Failed to commit!")
            raise

        return True

    def __repr__(self):
        return "<ChiruDatabase connected to `{}`>".format(self.db_uri)

    __str__ = __repr__


association_table = sa.Table(
    'channel_link', Base.metadata,
    sa.Column('channel_id', sa.BigInteger, sa.ForeignKey('channel.id')),
    sa.Column('link_id', sa.Integer, sa.ForeignKey('commit_link.id'))
)


class Channel(Base):
    """
    Represents a channel in logging and links.
    """
    __tablename__ = "channel"

    # No autoincrementing ID - this is provided to us by Discord as the snowflake.
    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=False)

    name = sa.Column(sa.String)

    links = relationship(
        "CommitLink",
        secondary=association_table,
        back_populates="channels")


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
