""" Tests for Game's finish.
"""

from server.db import map_db, game_db
from tests.lib.base_test import BaseTest


class TestFinish(BaseTest):

    MAP_NAME = 'test01'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        map_db.generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    def tearDown(self):
        game_db.truncate_tables()
        super().tearDown()

    def test_login_and_logout(self):
        games = game_db.get_all_games()
        self.assertEqual(len(games), 0)

        player = self.login()

        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0][0]
        self.assertIsNone(game.data, None)

        self.logout()

        self.assertTrue(self.wait_for_finished_games())
        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0][0]
        self.assertIsNotNone(game.data, None)
        self.assertIn(player['idx'], game.data)

    def test_login_and_disconnect(self):
        games = game_db.get_all_games()
        self.assertEqual(len(games), 0)

        player = self.login()

        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0][0]
        self.assertIsNone(game.data, None)

        self.reset_connection()

        self.assertTrue(self.wait_for_finished_games())
        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0][0]
        self.assertIsNotNone(game.data, None)
        self.assertIn(player['idx'], game.data)
