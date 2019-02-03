""" Server definitions.
"""
from enum import IntEnum


class Action(IntEnum):
    """ Client commands.
    """
    LOGIN = 1
    LOGOUT = 2
    MOVE = 3
    UPGRADE = 4
    TURN = 5
    PLAYER = 6
    GAMES = 7
    MAP = 10

    # Observer actions:
    OBSERVER = 100
    GAME = 101

    # This actions are not available for client:
    EVENT = 102


class Result(IntEnum):
    """ Server response codes.
    """
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    ACCESS_DENIED = 3
    INAPPROPRIATE_GAME_STATE = 4
    TIMEOUT = 5
    INTERNAL_SERVER_ERROR = 500
