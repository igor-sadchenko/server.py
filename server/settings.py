""" Base game/server configuration.
"""
from os import getenv, path

from attrdict import AttrDict

from entity.event import EventType


class BaseConfig(object):
    SRC_DIR = path.dirname(path.realpath(__file__))
    SERVER_ADDR = getenv('SERVER_ADDR', '127.0.0.1')
    SERVER_PORT = int(getenv('SERVER_PORT', 2000))

    DB_USER = getenv('DB_USER', 'postgres')
    DB_PASSWORD = getenv('DB_PASSWORD', 'password')
    DB_HOST = getenv('DB_HOST', 'pg')
    DB_PORT = getenv('DB_PORT', '5432')
    DB_NAME = getenv('DB_NAME', 'wgforge')
    PG_DATABASE_URL = 'postgresql://{user}:{password}@{hostname}:{port}/{db_name}'.format(
        user=DB_USER, password=DB_PASSWORD, hostname=DB_HOST, port=DB_PORT, db_name=DB_NAME
    )
    DB_URI = getenv('DB_URI', PG_DATABASE_URL)

    LOG_DIR = path.join(SRC_DIR, 'logs')
    DEFAULT_LOG_FILE_NAME = 'logs'

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

    REFUGEES_ARRIVAL_PROBABILITY = 10
    REFUGEES_NUMBER_RANGE = (1, 3)
    REFUGEES_COOLDOWN_COEFFICIENT = 5

    EVENT_COOLDOWNS_ON_START = {
        EventType.PARASITES_ASSAULT: PARASITES_POWER_RANGE[-1] * PARASITES_COOLDOWN_COEFFICIENT,
        EventType.HIJACKERS_ASSAULT: HIJACKERS_POWER_RANGE[-1] * HIJACKERS_COOLDOWN_COEFFICIENT,
        EventType.REFUGEES_ARRIVAL: REFUGEES_NUMBER_RANGE[-1] * REFUGEES_COOLDOWN_COEFFICIENT,
    }

    MAX_EVENT_MESSAGES = 5
    TIME_FORMAT = '%b %d %Y %I:%M:%S.%f'

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