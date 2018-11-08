""" Tests for action MOVE.
"""

from server.config import CONFIG
from server.db import map_db
from server.defs import Result
from tests.lib.base_test import BaseTest


class TestMove(BaseTest):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        map_db.reset_db()
        map_db.generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        map_db.reset_db()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.player = self.login()

    def tearDown(self):
        self.logout()
        super().tearDown()

    def test_reverse_on_move(self):
        train = self.player['trains'][0]
        line_idx = 18

        self.move_train(line_idx, train['idx'], -1)
        self.turn(turns_count=2)

        train = self.get_train(train['idx'])
        self.assertEqual(train['line_idx'], line_idx)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['speed'], -1)

        self.move_train(line_idx, train['idx'], 1)
        self.turn()

        train = self.get_train(train['idx'])
        self.assertEqual(train['line_idx'], line_idx)
        self.assertEqual(train['position'], 2)
        self.assertEqual(train['speed'], 1)

    def test_next_train_move(self):
        train = self.player['trains'][0]
        line_idx = 18
        next_line_idx = 6

        self.move_train(line_idx, train['idx'], -1)
        self.move_train(next_line_idx, train['idx'], -1)
        self.turn()

        train = self.get_train(train['idx'])
        self.assertEqual(train['line_idx'], line_idx)
        self.assertEqual(train['position'], 2)
        self.assertEqual(train['speed'], -1)

        self.turn(turns_count=3)

        train = self.get_train(train['idx'])
        self.assertEqual(train['line_idx'], next_line_idx)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['speed'], -1)

    def test_fuel_consuming(self):
        train = self.player['trains'][0]
        line_idx = 18
        turns_count = 3

        self.move_train(line_idx, train['idx'], -1)
        self.turn(turns_count=turns_count)

        train_after = self.get_train(train['idx'])
        self.assertEqual(train_after['fuel'], train['fuel'] - turns_count)
