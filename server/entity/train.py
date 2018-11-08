""" Train entity.
"""
from config import CONFIG
from entity.serializable import Serializable


class Train(Serializable):
    """ Train object represents train in the game which is able to transport some goods.

    Initialization:
        idx: unique index of the Train
        line_idx: unique index of line where the Train is placed
        position: position on the line at the current moment
        speed: speed of the Train (-1 or +1), negative - if the train is moving back on the line
        player_idx: unique index of the Player which is owner of the Train
        level: current level of the Train
        goods: quantity of some goods in the train at the current moment
        goods_type: PostType where first goods have been loaded into the train

    Has attributes:
        idx: unique index of the Train
        line_idx: unique index of line where the Train is placed
        position: position on the line at the current moment
        speed: speed of the Train (-1 or +1), negative - if the train is moving back on the line
        player_idx: unique index of the Player which is owner of the Train
        level: current level of the Train
        goods_capacity: maximum quantity of goods that the train can transport
        fuel: fuel amount in the train's tank at the current moment
        fuel_capacity: fuel tank size
        fuel_consumption: quantity of fuel that the train consumes per one unit of distance
        next_level_price: armor amount which player have to pay to get next level
        goods: quantity of some goods in the train at the current moment
        goods_type: PostType where first goods have been loaded into the train
        events: all events happened with the Train
        cooldown: the Train is blocked for this quantity of game ticks
    """
    def __init__(self, idx, line_idx=None, position=None, speed=0, player_idx=None, level=1, goods=0, goods_type=None):
        self.idx = idx
        self.line_idx = line_idx
        self.position = position
        self.speed = speed
        self.player_idx = player_idx
        self.level = level
        # Level-related attributes:
        self.goods_capacity = 0
        self.fuel_capacity = 0
        self.fuel_consumption = 0
        self.next_level_price = 0
        # Set level-related attributes from levels config:
        for key, value in CONFIG.TRAIN_LEVELS[self.level].items():
            setattr(self, key, value)
        self.fuel = self.fuel_capacity
        self.goods = goods
        self.goods_type = goods_type
        self.events = []
        self.cooldown = 0

    def set_level(self, next_lvl):
        self.level = next_lvl
        for key, value in CONFIG.TRAIN_LEVELS[self.level].items():
            setattr(self, key, value)

    def __repr__(self):
        return (
            '<Train(idx={}, line_idx={}, position={}, speed={}, player_idx={}, '
            'level={}, goods={}, goods_type={}, cooldown={})>'.format(
                self.idx, self.line_idx, self.position, self.speed, self.player_idx,
                self.level, self.goods, self.goods_type, self.cooldown
            )
        )
