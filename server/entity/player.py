""" Entity Player.
"""
import uuid

from config import CONFIG
from entity.point import Point
from entity.post import Post
from entity.serializable import Serializable
from entity.train import Train


class Player(Serializable):

    PLAYERS = {}  # All registered players.
    PROTECTED = ('security_key', 'turn_called', )
    DICT_TO_LIST = ('trains', )

    def __init__(self, name, security_key=None):
        self.idx = str(uuid.uuid4())
        self.name = name
        self.security_key = security_key
        self.trains = {}
        self.home = None
        self.town = None
        self.turn_called = False
        self.in_game = False
        self.rating = 0

    def __eq__(self, other):
        return self.idx == other.idx

    @staticmethod
    def create(name, security_key=None):
        """ Returns instance of class Player.
        """
        if name in Player.PLAYERS:
            player = Player.PLAYERS[name]
        else:
            Player.PLAYERS[name] = player = Player(name, security_key=security_key)
        return player

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
            '<Player(idx={}, name=\'{}\', home_point_idx={}, town_post_idx={}, '
            'turn_called={}, in_game={}, trains_idx=[{}])>'.format(
                self.idx, self.name, self.home.idx, self.town.idx, self.turn_called, self.in_game,
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
