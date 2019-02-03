""" Test Observer client-server protocol.
"""

import time

from server.config import CONFIG
from server.db import map_db
from server.db.session import session_ctx
from server.db.tasks import generate_replay01
from tests.lib.base_test import BaseTest
from tests.lib.server_connection import ServerConnection


class TestObserver(BaseTest):

    MAP_NAME = 'map03'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with session_ctx() as session:
            map_db.generate_maps(map_names=[TestObserver.MAP_NAME, ], active_map=TestObserver.MAP_NAME, session=session)
            generate_replay01(session)

    def test_observer_get_game_list(self):
        """ Connect as observer, get list of recorded games, verify list of games.
        """
        data = self.observer()
        self.assertIn('games', data)
        self.assertNotEqual(len(data['games']), 0)

    def test_observer_select_game(self):
        """ Select the test game, verify initial state.
        """
        self.observer()
        self.set_game(1)
        data = self.get_map(0)
        self.assertNotEqual(len(data), 0)
        self.assertIn('lines', data)
        lines = {x['idx']: x for x in data['lines']}
        self.assertEqual(lines[1]['points'][0], 1)
        self.assertEqual(lines[1]['points'][1], 2)
        trains = self.get_trains()
        self.assertEqual(trains, {})

    def test_observer_set_turn(self):
        """ Set turn and check.
        """
        self.observer()
        self.set_game(1)
        self.set_turn(3)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 3)
        self.assertEqual(train['line_idx'], 1)
        self.set_turn(10)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 2)
        self.assertEqual(train['line_idx'], 3)
        self.set_turn(0)
        trains = self.get_trains()
        self.assertEqual(trains, {})
        self.set_turn(100)
        train = self.get_train(1)
        self.assertEqual(train['speed'], -1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 176)
        self.set_turn(-1)
        trains = self.get_trains()
        self.assertEqual(trains, {})
        self.set_turn(1000)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)

    def test_read_coordinates(self):
        """ Get coordinates of points using layer 10.
        """
        self.observer()
        self.set_game(1)
        data = self.get_map(10)
        self.assertIn('idx', data.keys())
        self.assertIn('coordinates', data.keys())
        self.assertIn('size', data.keys())
        self.assertNotIn('lines', data.keys())
        self.assertNotIn('points', data.keys())

    def test_game_writes_turns_on_ticks(self):
        """ Verify if game on server writes to replay.db on game's tick.
        """
        user_conn = ServerConnection()

        self.login(connection=user_conn)
        time.sleep(CONFIG.TICK_TIME + 1)  # Wait for game tick.
        self.logout(connection=user_conn)
        time.sleep(2)  # Wait for DB commit.

        games = self.observer()['games']
        self.assertIsNotNone(games)
        my_games = [g for g in games if self.player_name in g['name']]
        self.assertEqual(len(my_games), 1)
        self.assertGreater(my_games[0]['length'], 0)

        user_conn.close()
