""" Game configurations.
"""
from os import getenv, path

from attrdict import AttrDict

from entity.event import EventType


class BaseConfig(object):
    """ Base configuration.
    """
    SRC_DIR = path.dirname(path.realpath(__file__))
    SERVER_ADDR = getenv('WG_FORGE_SERVER_ADDR', '127.0.0.1')
    SERVER_PORT = int(getenv('WG_FORGE_SERVER_PORT', 2000))
    MAP_DB_URI = getenv('MAP_DB_URI', 'sqlite:///' + path.join(SRC_DIR, 'map.db'))
    REPLAY_DB_URI = getenv('REPLAY_DB_URI', 'sqlite:///' + path.join(SRC_DIR, 'replay.db'))
    DB_URI = {
        'map': MAP_DB_URI,
        'replay': REPLAY_DB_URI,
    }

    ACTION_HEADER = 4
    RESULT_HEADER = 4
    MSGLEN_HEADER = 4
    RECEIVE_CHUNK_SIZE = 1024

    TICK_TIME = 10
    MAX_TICK_CALCULATION_TIME = 3
    TURN_TIMEOUT = TICK_TIME + MAX_TICK_CALCULATION_TIME

    MAP_NAME = 'map04'
    MAPS_FORMAT = 'yaml'
    MAPS_DISCOVERY = path.join(SRC_DIR, 'maps/*.yaml')

    TRAINS_COUNT = 8
    FUEL_ENABLED = False
    TRAIN_ALWAYS_DEVASTATED = True
    COLLISIONS_ENABLED = True

    HIJACKERS_ASSAULT_PROBABILITY = 20
    HIJACKERS_POWER_RANGE = (1, 3)
    HIJACKERS_COOLDOWN_COEFFICIENT = 5

    PARASITES_ASSAULT_PROBABILITY = 20
    PARASITES_POWER_RANGE = (1, 3)
    PARASITES_COOLDOWN_COEFFICIENT = 5

    REFUGEES_ARRIVAL_PROBABILITY = 1
    REFUGEES_NUMBER_RANGE = (1, 3)
    REFUGEES_COOLDOWN_COEFFICIENT = 5

    EVENT_COOLDOWNS_ON_START = {
        EventType.PARASITES_ASSAULT: PARASITES_POWER_RANGE[-1] * PARASITES_COOLDOWN_COEFFICIENT,
        EventType.HIJACKERS_ASSAULT: HIJACKERS_POWER_RANGE[-1] * HIJACKERS_COOLDOWN_COEFFICIENT,
        EventType.REFUGEES_ARRIVAL: REFUGEES_NUMBER_RANGE[-1] * REFUGEES_COOLDOWN_COEFFICIENT,
    }

    TOWN_LEVELS = AttrDict({
        1: {
            'population_capacity': 10,
            'product_capacity': 200,
            'armor_capacity': 200,
            'train_cooldown': 2,
            'next_level_price': 100,
        },
        2: {
            'population_capacity': 20,
            'product_capacity': 500,
            'armor_capacity': 500,
            'train_cooldown': 1,
            'next_level_price': 200,
        },
        3: {
            'population_capacity': 40,
            'product_capacity': 10000,
            'armor_capacity': 10000,
            'train_cooldown': 0,
            'next_level_price': None,
        },
    })

    TRAIN_LEVELS = AttrDict({
        1: {
            'goods_capacity': 40,
            'fuel_capacity': 400,
            'fuel_consumption': 1,
            'next_level_price': 40,
        },
        2: {
            'goods_capacity': 80,
            'fuel_capacity': 800,
            'fuel_consumption': 1,
            'next_level_price': 80,
        },
        3: {
            'goods_capacity': 160,
            'fuel_capacity': 1600,
            'fuel_consumption': 1,
            'next_level_price': None,
        },
    })


class TestingConfig(BaseConfig):
    """ Test configuration.
    """
    HIJACKERS_ASSAULT_PROBABILITY = 0
    PARASITES_ASSAULT_PROBABILITY = 0
    REFUGEES_ARRIVAL_PROBABILITY = 0
    EVENT_COOLDOWNS_ON_START = {}
    TRAIN_ALWAYS_DEVASTATED = False  # There is at least one test which awaits non-devastated train, TODO: check it
    MAX_LINE_LENGTH = 1000


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


SERVER_CONFIGS = {
    'testing': TestingConfig,
    'testing_with_events': TestingConfigWithEvents,
    'production': ProductionConfig,
}

CONFIG = SERVER_CONFIGS[getenv('WG_FORGE_SERVER_CONFIG', 'production')]
