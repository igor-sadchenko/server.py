""" Game server.
"""
import json
import socket
from functools import wraps
from socketserver import ThreadingTCPServer, BaseRequestHandler

from invoke import task

import errors
from config import CONFIG
from db import game_db
from defs import Action, Result
from entity.game import Game, GameState
from entity.observer import Observer
from entity.player import Player
from entity.serializable import Serializable
from logger import log


def login_required(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if self.game is None or self.player is None:
            raise errors.AccessDenied('Login required')
        else:
            return func(self, *args, **kwargs)
    return wrapped


class GameServerRequestHandler(BaseRequestHandler):

    HANDLERS = {}

    def __init__(self, *args, **kwargs):
        self.action = None
        self.message_len = None
        self.message = None
        self.data = None
        self.player = None
        self.game = None
        self.game_idx = None
        self.observer = None
        self.closed = None
        super(GameServerRequestHandler, self).__init__(*args, **kwargs)

    def setup(self):
        log.info('New connection from {}'.format(self.client_address), game=self.game)
        self.closed = False
        self.HANDLERS[id(self)] = self

    def handle(self):
        while not self.closed:
            data = self.request.recv(CONFIG.RECEIVE_CHUNK_SIZE)
            if data:
                self.data_received(data)
            else:
                self.closed = True

    @staticmethod
    def shutdown_all_sockets():
        for handler in GameServerRequestHandler.HANDLERS.values():
            handler.request.shutdown(socket.SHUT_RDWR)

    def finish(self):
        log.warn('Connection from {} lost'.format(self.client_address), game=self.game)
        if self.game is not None and self.player is not None and self.player.in_game:
            self.game.remove_player(self.player)
            if not self.observer:
                game_db.add_action(self.game_idx, Action.LOGOUT, player_idx=self.player.idx)
        self.HANDLERS.pop(id(self))

    def data_received(self, data):
        if self.data:
            data = self.data + data
            self.data = None

        if self.parse_data(data):
            log.info('[REQUEST] Player: {}, action: {!r}, message:\n{}'.format(
                self.player.idx if self.player is not None else self.client_address,
                Action(self.action), self.message), game=self.game)

            try:
                data = json.loads(self.message)
                if not isinstance(data, dict):
                    raise errors.BadCommand('The command\'s payload is not a dictionary')
                if self.observer:
                    self.write_response(*self.observer.action(self.action, data))
                else:
                    if self.action not in self.ACTION_MAP or self.action in CONFIG.HIDDEN_COMMANDS:
                        raise errors.BadCommand('No such action: {}'.format(self.action))
                    method = self.ACTION_MAP[self.action]
                    result, message = method(self, data)
                    self.write_response(result, message)

                    if not self.observer and self.action in self.REPLAY_ACTIONS:
                        game_db.add_action(self.game_idx, self.action, message=data, player_idx=self.player.idx)

            # Handle errors:
            except (json.decoder.JSONDecodeError, errors.BadCommand) as err:
                self.error_response(Result.BAD_COMMAND, err)
            except errors.AccessDenied as err:
                self.error_response(Result.ACCESS_DENIED, err)
            except errors.InappropriateGameState as err:
                self.error_response(Result.INAPPROPRIATE_GAME_STATE, err)
            except errors.Timeout as err:
                self.error_response(Result.TIMEOUT, err)
            except errors.ResourceNotFound as err:
                self.error_response(Result.RESOURCE_NOT_FOUND, err)
            except Exception:
                log.exception('Got unhandled exception on client command execution', game=self.game)
                self.error_response(Result.INTERNAL_SERVER_ERROR)
            finally:
                self.action = None
                self.message_len = None
                self.message = None

    def parse_data(self, data):
        """ Parses input command.
        returns: True if command parsing completed
        """
        # Read action:
        if self.action is None:
            if len(data) < CONFIG.ACTION_HEADER:
                self.data = data
                return False
            self.action = Action(int.from_bytes(data[0:CONFIG.ACTION_HEADER], byteorder='little'))
            data = data[CONFIG.ACTION_HEADER:]

        # Read size of message:
        if self.message_len is None:
            if len(data) < CONFIG.MSGLEN_HEADER:
                self.data = data
                return False
            self.message_len = int.from_bytes(data[0:CONFIG.MSGLEN_HEADER], byteorder='little')
            data = data[CONFIG.MSGLEN_HEADER:]

        # Read message:
        if self.message is None:
            if len(data) < self.message_len:
                self.data = data
                return False
            self.message = data[0:self.message_len].decode('utf-8') or '{}'
            self.data = data[self.message_len:]

        return True

    def write_response(self, result, message=None):
        resp_message = '' if message is None else message
        log.debug('[RESPONSE] Player: {}, result: {!r}, message:\n{}'.format(
            self.player.idx if self.player is not None else self.client_address,
            result, resp_message), game=self.game)
        self.request.sendall(result.to_bytes(CONFIG.RESULT_HEADER, byteorder='little'))
        self.request.sendall(len(resp_message).to_bytes(CONFIG.MSGLEN_HEADER, byteorder='little'))
        self.request.sendall(resp_message.encode('utf-8'))

    def error_response(self, result, exception=None):
        if exception is not None:
            str_exception = str(exception)
            log.error(str_exception, game=self.game)
            error = Serializable()
            error.set_attributes(error=str_exception)
            response_msg = error.to_json_str()
        else:
            response_msg = None
        self.write_response(result, response_msg)

    @staticmethod
    def check_keys(data: dict, keys, agg_func=all):
        if not agg_func([k in data for k in keys]):
            raise errors.BadCommand(
                'The command\'s payload does not contain all needed keys, '
                'following keys are expected: {}'.format(keys)
            )
        else:
            return True

    def on_login(self, data: dict):
        if self.game is not None or self.player is not None:
            raise errors.BadCommand('You are already logged in')

        self.check_keys(data, ['name'])
        player_name = data['name']
        password = data.get('password', None)

        player = Player.get(player_name, password=password)
        if not player.check_password(password):
            raise errors.AccessDenied('Password mismatch')

        game_name = data.get('game', 'Game of {}'.format(player_name))
        num_players = data.get('num_players', CONFIG.DEFAULT_NUM_PLAYERS)
        num_turns = data.get('num_turns', CONFIG.DEFAULT_NUM_TURNS)

        game = Game.get(game_name, num_players=num_players, num_turns=num_turns)

        game.check_state(GameState.INIT, GameState.RUN)
        player = game.add_player(player)
        self.game = game
        self.game_idx = game.game_idx
        self.player = player

        log.info('Player successfully logged in: {}'.format(player), game=self.game)
        message = self.player.to_json_str()

        return Result.OKEY, message

    @login_required
    def on_logout(self, _):
        log.info('Logout player: {}'.format(self.player.name), game=self.game)
        self.game.remove_player(self.player)
        self.closed = True
        return Result.OKEY, None

    @login_required
    def on_get_map(self, data: dict):
        self.check_keys(data, ['layer'])
        message = self.game.get_map_layer(self.player, data['layer'])
        return Result.OKEY, message

    @login_required
    def on_move(self, data: dict):
        self.check_keys(data, ['train_idx', 'speed', 'line_idx'])
        self.game.check_state(GameState.RUN)
        with self.player.lock:
            self.game.move_train(self.player, data['train_idx'], data['speed'], data['line_idx'])
        return Result.OKEY, None

    @login_required
    def on_turn(self, _):
        self.game.check_state(GameState.RUN)
        self.game.turn(self.player)
        return Result.OKEY, None

    @login_required
    def on_upgrade(self, data: dict):
        self.check_keys(data, ['trains', 'posts'], agg_func=any)
        self.game.check_state(GameState.RUN)
        with self.player.lock:
            self.game.make_upgrade(
                self.player, posts_idx=data.get('posts', []), trains_idx=data.get('trains', [])
            )
        return Result.OKEY, None

    @login_required
    def on_player(self, _):
        message = self.player.to_json_str()
        return Result.OKEY, message

    def on_list_games(self, _):
        games = Serializable()
        games.set_attributes(
            games=Game.get_all_active_games()
        )
        return Result.OKEY, games.to_json_str()

    def on_observer(self, _):
        if self.game or self.observer:
            raise errors.BadCommand('Impossible to connect as observer')
        else:
            self.observer = Observer()
            message = self.observer.games_to_json_str()
            return Result.OKEY, message

    ACTION_MAP = {
        Action.LOGIN: on_login,
        Action.LOGOUT: on_logout,
        Action.MAP: on_get_map,
        Action.MOVE: on_move,
        Action.UPGRADE: on_upgrade,
        Action.TURN: on_turn,
        Action.PLAYER: on_player,
        Action.GAMES: on_list_games,
        Action.OBSERVER: on_observer,
    }
    REPLAY_ACTIONS = {
        Action.LOGIN,
        Action.LOGOUT,
        Action.MOVE,
        Action.UPGRADE,
    }


@task
def run_server(_, address=CONFIG.SERVER_ADDR, port=CONFIG.SERVER_PORT, log_level='INFO'):
    """ Launches 'WG Forge' TCP server.
    """
    log.setLevel(log_level)
    ThreadingTCPServer.allow_reuse_address = True
    server = ThreadingTCPServer((address, port), GameServerRequestHandler)
    log.info('Serving on {}'.format(server.socket.getsockname()))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.warn('Server stopped by keyboard interrupt, shutting down...')
    finally:
        try:
            GameServerRequestHandler.shutdown_all_sockets()
            Game.stop_all_games()
            if log.is_queued:
                log.stop()
        finally:
            server.shutdown()
            server.server_close()
