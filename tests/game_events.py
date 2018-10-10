""" Tests for game random events.
"""

from server.config import CONFIG
from server.db.map import DbMap
from server.entity.event import Event, EventType
from tests.lib.base_test import BaseTest


class TestGameEvents(BaseTest):

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

    def test_refugees_arrival(self):
        turns_num = 6
        refugees_number = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_refugees = turns_ids[::CONFIG.REFUGEES_COOLDOWN_COEFFICIENT * refugees_number]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_refugees_arrival_event(
                town['events'],
                Event(EventType.REFUGEES_ARRIVAL, self.current_tick, refugees_number=refugees_number)
            )
            if self.current_tick in turns_with_refugees:
                self.assertTrue(check_event_result)
                self.assertEqual(town['population'], population_before_turn + refugees_number)
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['population'], population_before_turn)

    def test_hijackers_assault(self):
        turns_num = 10
        hijackers_power = 1  # From game config for testing.
        refugees_number = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_assault = turns_ids[::CONFIG.HIJACKERS_COOLDOWN_COEFFICIENT * hijackers_power]
        turns_with_refugees = turns_ids[::CONFIG.REFUGEES_COOLDOWN_COEFFICIENT * refugees_number]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            armor_before_turn = town['armor']
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_hijackers_assault_event(
                town['events'],
                Event(EventType.HIJACKERS_ASSAULT, self.current_tick, hijackers_power=hijackers_power)
            )
            if self.current_tick in turns_with_assault:
                self.assertTrue(check_event_result)
                armor_after_turn = armor_before_turn - hijackers_power
                if armor_after_turn >= 0:
                    self.assertEqual(town['armor'], armor_after_turn)
                    if self.current_tick in turns_with_refugees:
                        self.assertEqual(town['population'], population_before_turn + refugees_number)
                    else:
                        self.assertEqual(town['population'], population_before_turn)
                else:
                    self.assertEqual(town['armor'], 0)
                    if self.current_tick in turns_with_refugees:
                        self.assertEqual(
                            town['population'], max(population_before_turn + refugees_number - hijackers_power, 0))
                    else:
                        self.assertEqual(town['population'], max(population_before_turn - hijackers_power, 0))
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['armor'], armor_before_turn)
                if self.current_tick in turns_with_refugees:
                    self.assertEqual(town['population'], population_before_turn + refugees_number)
                else:
                    self.assertEqual(town['population'], population_before_turn)

    def test_parasites_assault(self):
        turns_num = 6
        parasites_power = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_assault = turns_ids[::CONFIG.PARASITES_COOLDOWN_COEFFICIENT * parasites_power]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            product_before_turn = town['product']
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_parasites_assault_event(
                town['events'],
                Event(EventType.PARASITES_ASSAULT, self.current_tick, parasites_power=parasites_power)
            )
            if self.current_tick in turns_with_assault:
                self.assertTrue(check_event_result)
                self.assertEqual(
                    town['product'], max(product_before_turn - parasites_power - population_before_turn, 0))
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['product'], max(product_before_turn - population_before_turn, 0))

    def test_event_messages_count(self):
        town_idx = self.player['town']['idx']
        self.turn()
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), 3)
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), 0)

        self.turn(turns_count=10)
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), CONFIG.MAX_EVENT_MESSAGES)
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), 0)

        self.turn(turns_count=20)
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), CONFIG.MAX_EVENT_MESSAGES)
        town = self.get_post(town_idx)
        self.assertEqual(len(town['events']), 0)

        test_line_idx = 13
        train_1 = self.player['trains'][0]
        train_2 = self.player['trains'][1]

        for _ in range(3):
            self.move_train(test_line_idx, train_1['idx'], 1)
            self.move_train(test_line_idx, train_2['idx'], 1)
            self.turn(turns_count=3)
        train_1 = self.get_train(train_1['idx'])
        self.assertEqual(len(train_1['events']), 3)
        train_1 = self.get_train(train_1['idx'])
        self.assertEqual(len(train_1['events']), 0)

        for _ in range(6):
            self.move_train(test_line_idx, train_1['idx'], 1)
            self.move_train(test_line_idx, train_2['idx'], 1)
            self.turn(turns_count=3)
        train_1 = self.get_train(train_1['idx'])
        self.assertEqual(len(train_1['events']), CONFIG.MAX_EVENT_MESSAGES)
        train_1 = self.get_train(train_1['idx'])
        self.assertEqual(len(train_1['events']), 0)
