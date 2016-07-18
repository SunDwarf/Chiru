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

        channel = self.session.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            # Create a new channel object.
            channel = Channel(id=channel_id, name=channel_name)

        # Create a new CommitLink.
        link = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if not link:
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
        Used by the Commits module to get commits for a repository.

        Automatically asyncified with the threadpool decorator.
        """
        repo = self.session.query(CommitLink).filter(CommitLink.repo_name == repo).first()
        if not repo:
            return []
        channels = [c for c in repo.channels]

        return channels

    @threadpool
    def get_repos_for_channel(self, channel: discord.Channel):
        """
        Used by the Commits module to get the repository
        """
        channel = self.session.query(Channel).filter(Channel.id == channel.id).first()
        if not channel:
            return []
        repos = [r for r in channel.links]

        return repos

    def __repr__(self):
        return "<ChiruDatabase connected to `{}`>".format(self.db_uri)

    __str__ = __repr__


association_table = sa.Table(
    'channel_link', Base.metadata,
    sa.Column('channel_id', sa.Integer, sa.ForeignKey('channel.id')),
    sa.Column('link_id', sa.Integer, sa.ForeignKey('commit_link.id'))
)


class Channel(Base):
    """
    This isn't a real channel object - it's just used to make querying easier in links.

    Maybe I'll add proper data to this Soom:tm:.
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

    @classmethod
    def get_secret(cls, repo_name: str) -> 'CommitLink':
        """
        Get the secret
        """
