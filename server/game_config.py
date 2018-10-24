""" Game configurations.
"""
from os import getenv

from attrdict import AttrDict


class BaseConfig(object):
    """ Base configuration.
    """
    TICK_TIME = 10
    MAX_TICK_CALCULATION_TIME = 5
    TURN_TIMEOUT = TICK_TIME + MAX_TICK_CALCULATION_TIME
    MAP_NAME = 'theMap'
    CURRENT_MAP_VERSION = 'map04'
    DEFAULT_TRAINS_COUNT = 8

    HIJACKERS_ASSAULT_PROBABILITY = 20
    HIJACKERS_POWER_RANGE = (1, 3)
    HIJACKERS_COOLDOWN_COEFFICIENT = 5

    PARASITES_ASSAULT_PROBABILITY = 20
    PARASITES_POWER_RANGE = (1, 3)
    PARASITES_COOLDOWN_COEFFICIENT = 5

    REFUGEES_ARRIVAL_PROBABILITY = 1
    REFUGEES_NUMBER_RANGE = (1, 3)
    REFUGEES_COOLDOWN_COEFFICIENT = 5

    TOWN_LEVELS = AttrDict({
        1: {
            'population_capacity': 10,
            'product_capacity': 200,
            'armor_capacity': 200,
            'train_cooldown_on_collision': 2,
            'next_level_price': 100,
        },
        2: {
            'population_capacity': 20,
            'product_capacity': 500,
            'armor_capacity': 500,
            'train_cooldown_on_collision': 1,
            'next_level_price': 200,
        },
        3: {
            'population_capacity': 40,
            'product_capacity': 10000,
            'armor_capacity': 10000,
            'train_cooldown_on_collision': 0,
            'next_level_price': None,
        },
    })

    TRAIN_LEVELS = AttrDict({
        1: {
            'goods_capacity': 40,
            # 'fuel_capacity': 400,
            # 'fuel_consumption': 1,
            'next_level_price': 40,
        },
        2: {
            'goods_capacity': 80,
            # 'fuel_capacity': 800,
            # 'fuel_consumption': 1,
            'next_level_price': 80,
        },
        3: {
            'goods_capacity': 160,
            # 'fuel_capacity': 1600,
            # 'fuel_consumption': 1,
            'next_level_price': None,
        },
    })


class TestingConfig(BaseConfig):
    """ Test configuration.
    """
    SERVER_ADDR = '127.0.0.1'
    SERVER_PORT = 2000
    HIJACKERS_ASSAULT_PROBABILITY = 0
    PARASITES_ASSAULT_PROBABILITY = 0
    REFUGEES_ARRIVAL_PROBABILITY = 0


class TestingConfigWithEvents(TestingConfig):
    """ Test configuration with random events.
    """
    HIJACKERS_ASSAULT_PROBABILITY = 100
    HIJACKERS_POWER_RANGE = (1, 1)
    PARASITES_ASSAULT_PROBABILITY = 100
    PARASITES_POWER_RANGE = (1, 1)
    REFUGEES_ARRIVAL_PROBABILITY = 100
    REFUGEES_NUMBER_RANGE = (1, 1)


class ProductionConfig(BaseConfig):
    """ Production configuration.
    """
    SERVER_ADDR = 'wgforge-srv.wargaming.net'
    SERVER_PORT = 443
    pass


SERVER_CONFIGS = {
    'testing': TestingConfig,
    'testing_with_events': TestingConfigWithEvents,
    'production': ProductionConfig,
}

CONFIG = SERVER_CONFIGS[getenv('WG_FORGE_SERVER_CONFIG', 'production')]
