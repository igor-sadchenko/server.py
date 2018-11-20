import uuid

from invoke import task

from config import CONFIG
from db import game_db, map_db
from db.models import Base
from db.session import session_ctx, Session
from defs import Action
from logger import log

__all__ = ['activate_map', 'generate_map', 'generate_all_maps', 'db_init', 'generate_replay', ]


@task
def generate_map(_, map_name=CONFIG.MAP_NAME):
    """ Generates a map in the DB.
    """
    map_db.generate_maps(map_names=[map_name, ], active_map=map_name)


@task
def generate_all_maps(_, active_map=CONFIG.MAP_NAME):
    """ Generates all maps in the DB.
    """
    map_db.generate_maps(active_map=active_map)


@task
def activate_map(_, map_name=CONFIG.MAP_NAME):
    """ Activates the maps in the DB.
    """
    map_db.set_active_map(map_name=map_name)


@task
def db_init(_):
    """ Initializes the DB.
    """
    Base.metadata.drop_all()
    Base.metadata.create_all()


@task
def generate_replay(_, replay_name=None):
    """ Generates game with actions in the DB for test purposes.
    """
    replay_generators = {
        'replay01': generate_replay01,
    }

    if replay_name is not None and replay_name not in replay_generators:
        err_msg = 'Error, unknown replay name: \'{}\', available: {}'.format(
            replay_name, ', '.join(replay_generators.keys()))
        log.error(err_msg)
        raise ValueError(err_msg)

    replays_to_generate = replay_generators.keys() if replay_name is None else [replay_name, ]
    with session_ctx() as session:
        for current_replay in replays_to_generate:
            replay_generator = replay_generators[current_replay]
            replay_generator(session)
            log.info('Replay \'{}\' has been generated'.format(current_replay))


def generate_replay01(session: Session):
    """ Generates replay for test purposes.
    """
    map_name = 'map03'

    player_name = 'replay_test_player'
    player_idx = str(uuid.uuid4())
    map_ = map_db.get_map_by_name(map_name, session=session)
    map_lines = map_db.get_lines_by_map_id(map_.id, session=session)

    game_db.add_player(player_idx, player_name, session=session)
    game_id = game_db.add_game('Test', map_.id, session=session)
    game_db.add_action(game_id, Action.LOGIN, {'name': player_name}, player_idx=player_idx, session=session)

    def insert_replay_move_and_turns(line_num: int, speed: int, train_idx: int, turns_count: int):
        """ Inserts into DB MOVE action + number of TURN actions.
        """
        line_idx = map_lines[line_num - 1].id
        game_db.add_action(
            game_id,
            Action.MOVE,
            {'line_idx': line_idx, 'speed': speed, 'train_idx': train_idx},
            player_idx=player_idx,
            session=session
        )
        for _ in range(turns_count):
            game_db.add_action(game_id, Action.TURN, session=session)

    def forward_move(line_num: int, count_turns: int):
        """ Forward move. Inner helper to simplify records formatting.
        """
        insert_replay_move_and_turns(line_num, 1, 1, count_turns)

    def reverse_move(line_idx: int, count_turns: int):
        """ Reverse move. Inner helper to simplify records formatting.
        """
        insert_replay_move_and_turns(line_idx, -1, 1, count_turns)

    forward = [
        (1, 3), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4),
        (19, 5), (38, 5), (57, 5), (76, 5), (95, 5), (114, 5), (133, 5), (152, 5), (171, 6)
    ]
    for move in forward:
        forward_move(*move)

    reverse = [
        (180, 3), (179, 4), (178, 4), (177, 4), (176, 4), (175, 4), (174, 4), (173, 4), (172, 4),
        (162, 5), (143, 5), (124, 5), (105, 5), (86, 5), (67, 5), (48, 5), (29, 5), (10, 6)
    ]
    for move in reverse:
        reverse_move(*move)
