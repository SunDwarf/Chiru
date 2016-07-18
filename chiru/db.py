"""
Chiru's database handler.

Connects the bot to a postgresql database, which transparently threadpools everything to make it async.
"""
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = sa.MetaData()
Base = declarative_base(metadata=metadata)

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
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=False)

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
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # author/repo, rather than just the repository name.
    # this makes querying easier.
    repo_name = sa.Column(sa.String)

    channels = relationship(
        "Channel",
        secondary=association_table,
        back_populates="links")

