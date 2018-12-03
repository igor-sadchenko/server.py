""" DB models.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from db.session import engine

Base = declarative_base(bind=engine)


class Map(Base):

    __tablename__ = 'maps'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=False, index=True, nullable=False)
    size_x = Column(Integer)
    size_y = Column(Integer)
    lines = relationship('Line', backref='map', lazy='dynamic')
    points = relationship('Point', backref='map', lazy='dynamic')
    posts = relationship('Post', backref='map', lazy='dynamic')

    def __repr__(self):
        return "<Map(id='{}', name='{}', size_x='{}', size_y='{}')>".format(
           self.id, self.name, self.size_x, self.size_y)


class Line(Base):

    __tablename__ = 'lines'

    id = Column(Integer, primary_key=True, index=True)
    length = Column(Integer, nullable=False)
    p0 = Column(Integer, nullable=False)
    p1 = Column(Integer, nullable=False)
    map_id = Column(Integer, ForeignKey('maps.id', ondelete='CASCADE'), index=True, nullable=False)

    def __repr__(self):
        return "<Line(id='{}', length='{}', p0='{}', p1='{}', map_id='{}')>".format(
           self.id, self.length, self.p0, self.p1, self.map_id)


class Point(Base):

    __tablename__ = 'points'

    id = Column(Integer, primary_key=True, index=True)
    map_id = Column(Integer, ForeignKey('maps.id', ondelete='CASCADE'), index=True, nullable=False)
    x = Column(Integer)
    y = Column(Integer)
    posts = relationship('Post', backref='point', lazy='dynamic')

    def __repr__(self):
        return "<Point(id='{}', map_id='{}', x='{}', y='{}')>".format(
           self.id, self.map_id, self.x, self.y)


class Post(Base):

    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Integer, nullable=False)
    population = Column(Integer)
    armor = Column(Integer)
    product = Column(Integer)
    replenishment = Column(Integer)
    map_id = Column(Integer, ForeignKey('maps.id', ondelete='CASCADE'), index=True, nullable=False)
    point_id = Column(Integer, ForeignKey('points.id', ondelete='CASCADE'), index=True, nullable=False)

    def __repr__(self):
        return (
            "<Post(id='{}', name='{}', type='{}', population='{}', armor='{}', "
            "product='{}', replenishment='{}', map_id='{}', point_id='{}')>".format(
                self.id, self.name, self.type, self.population, self.armor,
                self.product, self.replenishment, self.map_id, self.point_id
            )
        )


class Game(Base):

    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )
    map_id = Column(Integer, ForeignKey('maps.id', ondelete='SET NULL'), index=True)
    num_players = Column(Integer, nullable=False)
    num_turns = Column(Integer, nullable=False)
    data = Column(MutableDict.as_mutable(JSON))
    actions = relationship('Action', backref='game', lazy='dynamic')

    def __eq__(self, other):
        return self.id == other.id and self.created_at == other.created_at

    def __repr__(self):
        return "<Game(id='{}', name='{}', created_at='{}', map_id='{}', num_players='{}')>".format(
            self.id, self.name, self.created_at, self.map_id, self.num_players)

    def __hash__(self):
        return id(self)


class Action(Base):

    __tablename__ = 'actions'

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), index=True, nullable=False)
    code = Column(Integer, nullable=False)
    message = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
    player_id = Column(String, ForeignKey('players.id', ondelete='CASCADE'), index=True)

    def __eq__(self, other):
        return self.id == other.id and self.created_at == other.created_at

    def __repr__(self):
        return "<Action(id='{}', game_id='{}', code='{}', message='{}', created_at='{}', player_id='{}')>".format(
            self.id, self.game_id, self.code, self.message, self.created_at, self.player_id)


class Player(Base):

    __tablename__ = 'players'

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    def __eq__(self, other):
        return self.id == other.id and self.created_at == other.created_at

    def __repr__(self):
        return "<Player(id='{}', name='{}')>".format(self.id, self.name)
