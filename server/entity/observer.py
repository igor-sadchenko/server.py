""" Observer Entity. Handles requests when client connects to server as OBSERVER to watch replay(s).
"""

import errors
from config import CONFIG
from db import game_db, map_db
from defs import Action, Result
from entity.event import EventType
from entity.game import Game
from entity.player import Player
from entity.serializable import Serializable
from logger import log


def game_required(func):
    def wrapped(self, *args, **kwargs):
        if self.game is None:
            raise errors.BadCommand('A game is not chosen')
        else:
            return func(self, *args, **kwargs)
    return wrapped


class Observer(object):

    def __init__(self):
        self.game = None
        self.actions = []
        self.players = {}
        self.map_name = None
        self.game_name = None
        self.current_turn = 0
        self.current_action = 0
        self.max_turn = 0
        self.num_players = 0

    @staticmethod
    def check_keys(data: dict, keys, agg_func=all):
        if not agg_func([k in data for k in keys]):
            raise errors.BadCommand(
                'The command\'s payload does not contain all needed keys, '
                'following keys are expected: {}'.format(keys)
            )
        else:
            return True

    def games_to_json_str(self):
        """ Retrieves list of games.
        """
        games_list = []
        for game_data, game_length in game_db.get_all_games():
            game = {
                'idx': game_data.id,
                'name': game_data.name,
                'created_at': game_data.created_at.strftime(CONFIG.TIME_FORMAT),
                'map_idx': game_data.map_id,
                'length': game_length,
                'num_players': game_data.num_players,
                'ratings': game_data.ratings,
            }
            games_list.append(game)

        games = Serializable()
        games.set_attributes(games=games_list)
        return games.to_json_str()

    def reset_game(self):
        """ Resets the game to initial state.
        """
        self.game = Game(
            self.game_name,
            observed=True,
            num_players=self.num_players,
            map_name=self.map_name
        )
        self.players = {}
        self.current_turn = 0
        self.current_action = 0

    def action(self, action, data):
        """ Interprets observer's actions.
        """
        if action not in self.ACTION_MAP:
            raise errors.BadCommand('No such action: {}'.format(action))

        method = self.ACTION_MAP[action]
        return method(self, data)

    @game_required
    def on_get_map(self, data):
        """ Returns specified game map layer.
        """
        self.check_keys(data, ['layer'])
        message = self.game.get_map_layer(None, data['layer'])
        return Result.OKEY, message

    def game_turn(self, turns):
        """ Plays game turns.
        """
        sub_turn = 0
        events_map = {
            EventType.HIJACKERS_ASSAULT: (self.game.make_hijackers_assault, 'hijackers_power'),
            EventType.PARASITES_ASSAULT: (self.game.make_parasites_assault, 'parasites_power'),
            EventType.REFUGEES_ARRIVAL: (self.game.make_refugees_arrival, 'refugees_number'),
        }
        for action in self.actions[self.current_action:]:

            self.current_action += 1
            code = action.code
            message = action.message
            player_idx = action.player_id
            player = self.players.get(player_idx, None)

            if code == Action.LOGIN:
                player = Player(message['name'], password=message.get('password', None))
                player.idx = player_idx
                self.players[player_idx] = player
                self.game.add_player(player)

            elif code == Action.MOVE:
                self.game.move_train(
                    player, message['train_idx'], message['speed'], message['line_idx']
                )

            elif code == Action.UPGRADE:
                self.game.make_upgrade(
                    player, posts_idx=message.get('posts', []), trains_idx=message.get('trains', [])
                )

            elif code == Action.TURN:
                self.game.tick()
                sub_turn += 1
                self.current_turn += 1

            elif code == Action.EVENT:
                event, power_attr = events_map[message['type']]
                event(message[power_attr])

            elif code == Action.LOGOUT:
                self.game.remove_player(player)

            else:
                log.error('Unknown action code: {}'.format(code))

            if sub_turn >= turns:
                break

    @game_required
    def on_turn(self, data):
        """ Sets specified game turn.
        """
        self.check_keys(data, ['idx'])

        turn = data['idx']
        turn = min(max(turn, 0), self.max_turn)

        if turn == self.current_turn:
            return Result.OKEY, None

        delta_turn = turn - self.current_turn
        if delta_turn > 0:
            self.game_turn(delta_turn)
        elif delta_turn < 0:
            self.reset_game()
            if turn > 0:
                self.game_turn(turn)

        self.current_turn = turn

        return Result.OKEY, None

    def on_game(self, data):
        """ Chooses a game.
        """
        self.check_keys(data, ['idx'])

        game_idx = data['idx']
        game = game_db.get_game(game_idx)
        if game is None:
            raise errors.ResourceNotFound('Game index not found, index: {}'.format(game_idx))

        game, game_length = game
        game_map = map_db.get_map_by_id(game.map_id)
        self.game = None
        self.game_name = game.name
        self.num_players = game.num_players
        self.map_name = game_map.name
        self.actions = game_db.get_all_actions(game_idx)
        self.max_turn = game_length
        self.reset_game()
        log.info('Observer selected game: {}'.format(self.game_name))

        return Result.OKEY, None

    def on_observer(self, _):
        """ Returns list of games.
        """
        message = self.games_to_json_str()
        return Result.OKEY, message

    ACTION_MAP = {
        Action.MAP: on_get_map,
        Action.TURN: on_turn,
        Action.GAME: on_game,
        Action.OBSERVER: on_observer,
    }
