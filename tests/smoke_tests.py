""" Simple smoke tests.
"""
import json

from server.db.map import DbMap
from server.defs import Action, Result
from tests.lib.base_test import BaseTest


class TestSmoke(BaseTest):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        DbMap().generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        DbMap().reset_db()
        super().tearDownClass()

    def test_login_logout(self):
        """ Test logout.
        """
        data = self.login()
        self.assertIn('idx', data)
        player_idx = data['idx']
        self.assertIsNotNone(player_idx)
        self.logout()

    def test_get_map_layer_0(self):
        """ Test layer_to_json_str and from_json_str for layer 0.
        """
        self.login()

        result, message = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)

        self.assertIn('idx', map_data)
        self.assertIn('name', map_data)
        self.assertIn('lines', map_data)
        self.assertIn('points', map_data)
        self.assertNotIn('posts', map_data)
        self.assertNotIn('trains', map_data)
        self.assertNotIn('size', map_data)
        self.assertNotIn('coordinates', map_data)
        self.assertNotIn('ratings', map_data)

        self.logout()

    def test_get_map_layer_1(self):
        """ Test layer_to_json_str and from_json_str for layer 1.
        """
        self.login()

        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)

        self.assertIn('idx', map_data)
        self.assertIn('posts', map_data)
        self.assertIn('trains', map_data)
        self.assertIn('ratings', map_data)
        self.assertNotIn('name', map_data)
        self.assertNotIn('lines', map_data)
        self.assertNotIn('points', map_data)
        self.assertNotIn('size', map_data)
        self.assertNotIn('coordinates', map_data)

        posts = {x['name']: x for x in map_data['posts']}
        self.assertIn('market-small', posts)
        self.assertIn('market-medium', posts)
        self.assertIn('market-big', posts)
        self.assertEqual(posts['market-small']['replenishment'], 1)
        self.assertEqual(posts['market-medium']['replenishment'], 1)
        self.assertEqual(posts['market-big']['replenishment'], 2)

        self.logout()

    def test_get_map_layer_10(self):
        """ Test layer_to_json_str and from_json_str for layer 10.
        """
        self.login()

        result, message = self.do_action(Action.MAP, {'layer': 10})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)

        self.assertIn('idx', map_data)
        self.assertIn('size', map_data)
        self.assertIn('coordinates', map_data)
        self.assertNotIn('posts', map_data)
        self.assertNotIn('trains', map_data)
        self.assertNotIn('name', map_data)
        self.assertNotIn('lines', map_data)
        self.assertNotIn('points', map_data)
        self.assertNotIn('ratings', map_data)

        self.logout()

    def test_move_train(self):
        """ Get train belongs to the Player.
        """
        # Login for get player id.
        player = self.login()
        player_idx = player['idx']
        train_idx = player['trains'][0]['idx']
        n = 0

        # Check train's owner.
        train = self.get_train(train_idx)
        self.assertEqual(train['player_idx'], player_idx)

        # Begin moving.
        self.move_train(1 + n, train_idx, 1)
        self.turn()
        self.assertGreater(self.get_train_position(train_idx), 0)

        self.move_train_until_switch(7 + n, train_idx, 1)
        self.move_train_until_switch(8 + n, train_idx, 1)
        self.move_train_until_switch(9 + n, train_idx, 1)
        self.move_train_until_switch(10 + n, train_idx, 1)
        self.move_train_until_switch(11 + n, train_idx, 1)
        self.move_train_until_switch(12 + n, train_idx, 1)
        self.move_train_until_switch(1 + n, train_idx, -1)
        for _ in range(self.get_train_position(train_idx)):
            self.turn()
        self.assertEqual(self.get_train_position(train_idx), 0)
        self.assertEqual(self.get_train_line(train_idx), 1)

        self.logout()

    def test_transport_product(self):
        """ Transports product from shop_one to town_one.
        """
        player = self.login()
        player_idx = player['idx']
        train_idx = player['trains'][0]['idx']
        post_idx = player['town']['idx']
        start_product = player['town']['product']
        population = player['town']['population']

        train = self.get_train(train_idx)
        self.assertEqual(train['player_idx'], player_idx)
        self.assertEqual(int(train['position']), 0)
        self.assertNotEqual(int(train['goods_capacity']), 0)
        self.assertEqual(int(train['goods']), 0)
        self.assertEqual(int(train['speed']), 0)

        self.move_train(1, train_idx, 1)
        self.turn()

        train = self.get_train(train_idx)
        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 1)
        self.assertEqual(int(train['goods']), 5)

        self.move_train(1, train_idx, -1)
        self.turn()

        train = self.get_train(train_idx)
        self.assertEqual(int(train['speed']), 0)
        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 0)
        self.assertEqual(int(train['goods']), 0)

        post = self.get_post(post_idx)
        turns_count = 2
        self.assertEqual(int(post['product']), start_product - population * turns_count + 5)

        self.logout()

    def test_wrong_actions(self):
        """ Test error codes on wrong action messages.
        """
        result, _ = self.do_action(Action.LOGIN, {'layer': 10})
        self.assertEqual(Result.BAD_COMMAND, result)
        result, _ = self.do_action(Action.LOGIN, '1234567890', is_raw=True)
        self.assertEqual(Result.BAD_COMMAND, result)
