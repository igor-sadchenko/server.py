""" Game/server configurations.
"""
from os import getenv

try:
    from settings_local import LocalConfig as Config
except ImportError as e:
    from settings import BaseConfig as Config


class TestingConfig(Config):
    """ Test configuration.
    """
    HIJACKERS_ASSAULT_PROBABILITY = 0
    PARASITES_ASSAULT_PROBABILITY = 0
    REFUGEES_ARRIVAL_PROBABILITY = 0
    EVENT_COOLDOWNS_ON_START = {}
    TRAIN_ALWAYS_DEVASTATED = False  # There is at least one test which awaits non-devastated train, TODO: check it
    MAX_LINE_LENGTH = 1000
    FUEL_ENABLED = True
    DB_URI = getenv('DB_URI', 'postgresql://wgforge:wgforge@127.0.0.1:5432/wgforge')


class TestingConfigWithEvents(TestingConfig):
    """ Test configuration with random events.
    """
    HIJACKERS_ASSAULT_PROBABILITY = 100
    HIJACKERS_POWER_RANGE = (1, 1)
    PARASITES_ASSAULT_PROBABILITY = 100
    PARASITES_POWER_RANGE = (1, 1)
    REFUGEES_ARRIVAL_PROBABILITY = 100
    REFUGEES_NUMBER_RANGE = (1, 1)


class ProductionConfig(Config):
    """ Production configuration.
    """
    pass


SERVER_CONFIGS = {
    'testing': TestingConfig,
    'testing_with_events': TestingConfigWithEvents,
    'production': ProductionConfig,
}

CONFIG = SERVER_CONFIGS[getenv('SERVER_CONFIG', 'production')]
