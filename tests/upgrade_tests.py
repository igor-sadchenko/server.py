""" Tests for action UPGRADE.
"""

from server.config import CONFIG
from server.db.map import DbMap
from server.defs import Result
from tests.lib.base_test import BaseTest


class TestUpgrade(BaseTest):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        DbMap().generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        DbMap().reset_db()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.player = self.login()

    def tearDown(self):
        self.logout()
        super().tearDown()

    def test_upgrade_train(self):
        test_line_idx = 18
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_until_stop(test_line_idx, train_1['idx'], -1)
        self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],))
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor - armor_to_pay)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'] + 1)
        self.assertGreater(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertGreater(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_train_when_no_enough_armor(self):
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        start_armor = self.get_post(town['idx'])['armor']
        armor_to_pay = train_1['next_level_price']

        # Check that player have no enough armor to upgrade train:
        self.assertLess(start_armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], start_armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_if_train_not_in_town_1(self):
        test_line_idx_1 = 18
        test_line_idx_2 = 13
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_until_stop(test_line_idx_1, train_1['idx'], -1)
        self.move_train_until_stop(test_line_idx_1, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])
        self.move_train_until_stop(test_line_idx_2, train_1['idx'], 1)

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_if_train_not_in_town_2(self):
        test_line_idx_1 = 18
        test_line_idx_2 = 1
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_until_stop(test_line_idx_1, train_1['idx'], -1)
        self.move_train_until_stop(test_line_idx_1, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])
        self.move_train_until_stop(test_line_idx_2, train_1['idx'], 1)

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_train_when_no_next_level(self):
        test_line_idx = 18
        wait_for_replenishment = 5
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        for _ in range(len(CONFIG.TRAIN_LEVELS.keys()) - 2):
            self.move_train_until_stop(test_line_idx, train_1['idx'], -1)
            self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
            self.turn(wait_for_replenishment)

            curr_train_1 = self.get_train(train_1['idx'])
            curr_train_2 = self.get_train(train_2['idx'])
            armor = self.get_post(town['idx'])['armor']
            armor_to_pay = curr_train_1['next_level_price']
            # Check that player have enough armor to upgrade train:
            self.assertGreaterEqual(armor, armor_to_pay)

            self.upgrade(trains=(train_1['idx'],))
            map_data = self.get_map(1)

            self.assertEqual(self.get_post(town['idx'])['armor'], armor - armor_to_pay)
            self.assertEqual(map_data['train'][0]['level'], curr_train_1['level'] + 1)
            self.assertGreater(map_data['train'][0]['goods_capacity'], curr_train_1['goods_capacity'])
            self.assertGreater(map_data['train'][0]['next_level_price'], curr_train_1['next_level_price'])
            self.assertEqual(map_data['train'][1]['level'], curr_train_2['level'])
            self.assertEqual(map_data['train'][1]['goods_capacity'], curr_train_2['goods_capacity'])
            self.assertEqual(map_data['train'][1]['next_level_price'], curr_train_2['next_level_price'])

        # Try to upgrade train to non-existing level:
        self.move_train_until_stop(test_line_idx, train_1['idx'], -1)
        self.move_train_until_stop(test_line_idx, train_1['idx'], 1)

        curr_train_1 = self.get_train(train_1['idx'])
        curr_train_2 = self.get_train(train_2['idx'])
        armor = self.get_post(town['idx'])['armor']

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], curr_train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], curr_train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], curr_train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], curr_train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], curr_train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], curr_train_2['next_level_price'])

    def test_upgrade_town(self):
        trips = 20
        test_line_idx = 18
        wait_for_replenishment = 6
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        for _ in range(trips):
            self.move_train_until_stop(test_line_idx, train_1['idx'], -1)
            self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
            self.turn(wait_for_replenishment)

        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor_capacity'])
        # Check that player have enough armor to upgrade town:
        self.assertGreaterEqual(armor, town['next_level_price'])

        train_1_partial_unload = self.get_train(train_1['idx'])
        self.upgrade(posts=(town['idx'],))
        self.turn()
        map_data = self.get_map(1)
        town_now = self.get_post(town['idx'])

        self.assertEqual(town_now['armor'], armor - town['next_level_price'] + train_1_partial_unload['goods'])
        self.assertEqual(town_now['level'], town['level'] + 1)
        self.assertGreater(town_now['population_capacity'], town['population_capacity'])
        self.assertGreater(town_now['product_capacity'], town['product_capacity'])
        self.assertGreater(town_now['armor_capacity'], town['armor_capacity'])
        self.assertGreater(town_now['next_level_price'], town['next_level_price'])
        self.assertTrue(
            town_now['train_cooldown'] < town['train_cooldown']
            or town_now['train_cooldown'] == 0
        )

        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_town_when_no_enough_armor(self):
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        # Check that player have no enough armor to upgrade town:
        self.assertLess(town['armor'], town['next_level_price'])

        self.upgrade(posts=(town['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)
        town_now = self.get_post(town['idx'])

        self.assertEqual(town_now['armor'], town['armor'])
        self.assertEqual(town_now['level'], town['level'])
        self.assertEqual(town_now['population_capacity'], town['population_capacity'])
        self.assertEqual(town_now['product_capacity'], town['product_capacity'])
        self.assertEqual(town_now['armor_capacity'], town['armor_capacity'])
        self.assertEqual(town_now['next_level_price'], town['next_level_price'])
        self.assertEqual(town_now['train_cooldown'], town['train_cooldown'])

        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])
