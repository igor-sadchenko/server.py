import sqlite3
import sys

from invoke import task

from config import CONFIG
from db.map import DbMap
from db.replay import REPLAY_GENERATORS, DbReplay
from db.session import replay_session_ctx

__all__ = ['db_shell', 'generate_replay', 'generate_map', 'db_init']


@task
def db_shell(_, db_name='map'):
    """ Creates a minimal SQLite shell session for experiments.
    """
    if db_name not in CONFIG.DB_URI:
        print("Error, unknown DB name: '{}', available: {}".format(db_name, ', '.join(CONFIG.DB_URI.keys())))
        sys.exit(1)

    con = sqlite3.connect(CONFIG.DB_URI[db_name].replace('sqlite:///', 'file:'), uri=True)
    con.isolation_level = None
    cur = con.cursor()
    buffer = ''
    shell_prompt = '{}=> '.format(db_name)
    shell_prompt_non_completed = '{}-> '.format(db_name)

    print("Enter your SQL commands to execute in sqlite3.\n"
          "Enter a blank line to exit.")

    curr_shell_prompt = shell_prompt
    while True:
        line = input(curr_shell_prompt)
        if line == '':
            break
        buffer += line
        if sqlite3.complete_statement(buffer):
            try:
                buffer = buffer.strip()
                cur.execute(buffer)
                if buffer.lstrip().upper().startswith('SELECT'):
                    for line in cur.fetchall():
                        print(line)
            except sqlite3.Error as e:
                print("An error occurred: {}".format(e.args[0]))
            buffer = ''
            curr_shell_prompt = shell_prompt
        else:
            curr_shell_prompt = shell_prompt_non_completed

    con.close()
    sys.exit(0)


@task
def generate_replay(_, replay_name=None):
    """ Generates 'replay.db'.
    """
    if replay_name is not None and replay_name not in REPLAY_GENERATORS:
        print("Error, unknown replay name: '{}', available: {}".format(
            replay_name, ', '.join(REPLAY_GENERATORS.keys())))
        sys.exit(1)
    database = DbReplay()
    database.reset_db()
    replays_to_generate = REPLAY_GENERATORS.keys() if replay_name is None else [replay_name, ]
    with replay_session_ctx() as session:
        for current_replay in replays_to_generate:
            replay_generator = REPLAY_GENERATORS[current_replay]
            replay_generator(database, session)
            print("Replay '{}' has been generated.".format(current_replay))
    sys.exit(0)


@task
def generate_map(_, map_name=CONFIG.MAP_NAME):
    """ Generates 'map.db'.
    """
    DbMap().generate_maps(map_names=[map_name, ], active_map=map_name)


@task
def db_init(_):
    """ Initializes all databases.
    """
    DbMap().reset_db()
    DbReplay.reset_db()
