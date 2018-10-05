""" Base test class.
"""

import json
import unittest
from datetime import datetime

from server.config import CONFIG
from server.defs import Action, Result
from tests.lib.server_connection import ServerConnection


class BaseTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        self.test_start = datetime.now().strftime('%H:%M:%S.%f')
        self.player_name = 'PLAYER_{}_{}'.format(self.id(), self.test_start)
        self.game_name = 'GAME_{}_{}'.format(self.id(), self.test_start)
        self.current_tick = None
        self._connection = None

    def setUp(self):
        self.current_tick = 0

    def tearDown(self):
        if self._connection is not None:
            self._connection.close()

    @property
    def connection(self):
        if self._connection is None:
            self._connection = ServerConnection()
        return self._connection

    def do_action(self, action, data='', exp_result=None, is_raw=False, connection=None, **kwargs):
        connection = self.connection if connection is None else connection
        result, message = connection.send_action(action, data, is_raw=is_raw, **kwargs)
        if exp_result is not None:
            self.assertEqual(exp_result, result)
        return result, message

    def login(self, name=None, game=None, security_key=None, num_players=None, exp_result=Result.OKEY, **kwargs):
        message = {'name': self.player_name if name is None else name}
        if game is not None:
            message['game'] = game
        if security_key is not None:
            message['security_key'] = security_key
        if num_players is not None:
            message['num_players'] = num_players
        _, message = self.do_action(
            Action.LOGIN,
            message,
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def logout(self, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.LOGOUT,
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def turn(self, turns_count=1, exp_result=Result.OKEY, **kwargs):
        message = None
        for _ in range(turns_count):
            _, message = self.do_action(
                Action.TURN,
                exp_result=exp_result,
                **kwargs
            )
            if exp_result == Result.OKEY:
                self.current_tick += 1
        return json.loads(message) if message else None

    def get_map(self, layer, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.MAP,
            {'layer': layer},
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message)

    def move_train(self, line_idx, train_idx, speed, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.MOVE,
            {
                'train_idx': train_idx,
                'line_idx': line_idx,
                'speed': speed,
            },
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def get_trains(self, **kwargs):
        map_data = self.get_map(1, **kwargs)
        return {x['idx']: x for x in map_data['train']}

    def get_train(self, train_idx, **kwargs):
        trains = self.get_trains(**kwargs)
        self.assertIn(train_idx, trains)
        return trains[train_idx]

    def get_posts(self, **kwargs):
        map_data = self.get_map(1, **kwargs)
        return {x['idx']: x for x in map_data['post']}

    def get_post(self, post_idx, **kwargs):
        posts = self.get_posts(**kwargs)
        self.assertIn(post_idx, posts)
        return posts[post_idx]

    def get_train_line(self, train_idx, **kwargs):
        train = self.get_train(train_idx, **kwargs)
        return train['line_idx']

    def get_train_speed(self, train_idx, **kwargs):
        train = self.get_train(train_idx, **kwargs)
        return train['speed']

    def get_train_position(self, train_idx, **kwargs):
        train = self.get_train(train_idx, **kwargs)
        return train['position']

    @staticmethod
    def check_collision_event(events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['train'] == ok_event.train
                    and event['tick'] == ok_event.tick):
                return True
        return False

    @staticmethod
    def check_refugees_arrival_event(events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['refugees_number'] == ok_event.refugees_number
                    and event['tick'] == ok_event.tick):
                return True
        return False

    @staticmethod
    def check_hijackers_assault_event(events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['hijackers_power'] == ok_event.hijackers_power
                    and event['tick'] == ok_event.tick):
                return True
        return False

    @staticmethod
    def check_parasites_assault_event(events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['parasites_power'] == ok_event.parasites_power
                    and event['tick'] == ok_event.tick):
                return True
        return False

    def move_train_until_switch(self, next_line_idx, train_idx, speed, **kwargs):
        self.move_train(next_line_idx, train_idx, speed, **kwargs)
        for _ in range(CONFIG.MAX_LINE_LENGTH):
            self.turn(**kwargs)
            if self.get_train_line(train_idx, **kwargs) == next_line_idx:
                break
        else:
            self.fail('The train {} is not able to reach the line {} in {} turns'.format(
                train_idx, next_line_idx, CONFIG.MAX_LINE_LENGTH))

    def move_train_until_stop(self, line_idx, train_idx, speed, **kwargs):
        self.move_train(line_idx, train_idx, speed, **kwargs)
        for _ in range(CONFIG.MAX_LINE_LENGTH):
            self.turn(**kwargs)
            if self.get_train_speed(train_idx, **kwargs) == 0:
                break
        else:
            self.fail('The train {} is not able to reach the end of line {} in {} turns'.format(
                train_idx, line_idx, CONFIG.MAX_LINE_LENGTH))

    def upgrade(self, posts=(), trains=(), exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.UPGRADE,
            {
                'post': posts,
                'train': trains,
            },
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def observer(self, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.OBSERVER,
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def set_turn(self, turn_idx, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.TURN,
            {'idx': turn_idx},
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None

    def set_game(self, game_idx, exp_result=Result.OKEY, **kwargs):
        _, message = self.do_action(
            Action.GAME,
            {'idx': game_idx},
            exp_result=exp_result,
            **kwargs
        )
        return json.loads(message) if message else None
