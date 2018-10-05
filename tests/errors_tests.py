""" Tests for server errors.
"""

from server.db.map import DbMap
from server.defs import Result
from tests.lib.base_test import BaseTest


class TestErrors(BaseTest):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        DbMap().generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        DbMap().reset_db()
        super().tearDownClass()

    def test_login(self):
        security_key = 'you-will-never-guess'
        wrong_security_key = 'i-will-try-to-guess'
        self.login(security_key=security_key)
        message = self.login(security_key=wrong_security_key, exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn('Security key mismatch', message['error'])

    def test_get_map(self):
        non_existing_map_layer = 999999
        message = self.get_map(0, exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn('Login required', message['error'])
        self.login()
        message = self.get_map(non_existing_map_layer, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn('Map layer not found', message['error'])

    def test_move_train(self):
        test_line_idx = 13
        next_line_idx = 2
        not_connected_line_idx = 10
        non_existing_line_idx = 999999
        non_existing_train_idx = 999999
        player = self.login()
        train_1 = player['train'][0]
        train_2 = player['train'][1]
        train_3 = player['train'][2]

        message = self.move_train(non_existing_line_idx, train_1['idx'], 1, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn('Line index not found', message['error'])

        message = self.move_train(test_line_idx, non_existing_train_idx, 1, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn('Train index not found', message['error'])

        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        message = self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('The train is under cooldown', message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_3['idx'], 0)
        message = self.move_train(next_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('The train is standing on the line', message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('The end of the train\'s line is not connected to the next line', message['error'])

        self.move_train(test_line_idx, train_3['idx'], -1)
        self.turn(turns_count=2)
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('The beginning of the train\'s line is not connected to the next line', message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('The train is not able to switch the current line to the next line', message['error'])
