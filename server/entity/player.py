""" Entity Player.
"""
import uuid
from threading import Lock

from config import CONFIG
from db import game_db
from entity.point import Point
from entity.post import Post
from entity.serializable import Serializable
from entity.train import Train


class Player(Serializable):

    PROTECTED = {'password', 'turn_called', 'db', 'lock', }
    DICT_TO_LIST = {'trains', }

    def __init__(self, name, password=None, idx=None):
        self.idx = str(uuid.uuid4()) if idx is None else idx
        self.name = name
        self.password = password
        self.trains = {}
        self.home = None
        self.town = None
        self.turn_called = False
        self.in_game = False
        self.rating = 0
        self.lock = Lock()

    def __eq__(self, other):
        return self.idx == other.idx

    @staticmethod
    def get(name, **kwargs):
        """ Returns instance of class Player.
        """
        player_data = game_db.get_player_by_name(name)
        if player_data is None:
            player = Player(name, **kwargs)
            game_db.add_player(player.idx, player.name, player.password)
        else:
            player = Player(player_data.name, password=player_data.password, idx=player_data.id)
        return player

    def check_password(self, password):
        """ Checks password matching.
        """
        return self.password == password

    def add_train(self, train: Train):
        """ Adds train to the player.
        """
        train.player_idx = self.idx
        self.trains[train.idx] = train

    def set_home(self, point: Point, post: Post):
        """ Sets home point.
        """
        post.player_idx = self.idx
        self.home = point
        self.town = post

    def __repr__(self):
        return (
            '<Player(idx={}, name=\'{}\', home_point={}, town_post={}, '
            'turn_called={}, in_game={}, trains_idx=[{}])>'.format(
                self.idx, self.name, self.home, self.town, self.turn_called, self.in_game,
                ', '.join([str(idx) for idx in self.trains]))
        )

    def recalculate_rating(self):
        """ Calculates player's rating.
        """
        self.rating = self.town.population * 1000
        self.rating += (self.town.product + self.town.armor)
        level_price_sum = 0
        for train in self.trains.values():
            for level in range(1, train.level):
                level_price_sum += CONFIG.TRAIN_LEVELS[level]['next_level_price']
        for level in range(1, self.town.level):
            level_price_sum += CONFIG.TOWN_LEVELS[level]['next_level_price']
        self.rating += (level_price_sum * 2)
        return self.rating
