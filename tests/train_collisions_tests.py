""" Tests for train collisions.
"""

from server.db.map import DbMap
from server.defs import Result
from server.entity.event import Event, EventType
from tests.lib.base_test import BaseTest


class TestTrainCollisions(BaseTest):

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

    def test_collision_in_same_position_move_about(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_same_position_move_towards(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_on_line_with_stopped_1(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_1['idx'], 0)
        self.turn()
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_on_line_with_stopped_2(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_2['idx'], 0)
        self.turn()
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_goods_destroyed(self):
        test_line_idx = 1
        town_idx = self.player['town']['idx']
        start_product = self.player['town']['product']
        population = self.player['town']['population']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])
        self.assertEqual(map_data['train'][0]['goods'], 0)
        self.assertEqual(map_data['train'][1]['goods'], 0)
        # No new product arrived:
        self.assertEqual(self.get_post(town_idx)['product'], start_product - population * self.current_tick)

    def test_collision_in_point_1(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(13, train_1['idx'], 1)
        self.move_train_until_stop(1, train_2['idx'], 1)
        self.move_train_until_stop(7, train_2['idx'], 1)
        self.move_train(2, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_point_2(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(13, train_1['idx'], 1)
        self.move_train(13, train_2['idx'], 1)
        self.turn(2)
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_post_1(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(1, train_1['idx'], 1)
        self.move_train(1, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_post_2(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_until_stop(1, train_1['idx'], 1)
        self.move_train_until_stop(13, train_2['idx'], 1)
        self.move_train_until_stop(2, train_2['idx'], -1)
        self.move_train(7, train_2['idx'], -1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_no_collision_in_town(self):
        self.turn()
        map_data = self.get_map(1)
        self.assertEqual(map_data['train'][0]['event'], [])
        self.assertEqual(map_data['train'][1]['event'], [])

    def test_collision_with_3_trains(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        train_3 = self.player['train'][2]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_3['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_3['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][2]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][2]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])
        self.assertEqual(map_data['train'][2]['line_idx'], train_3['line_idx'])
        self.assertEqual(map_data['train'][2]['position'], train_3['position'])

    def test_cooldown_on_collision(self):
        test_line_idx = 13
        town = self.get_post(self.player['town']['idx'])
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.assertEqual(train_1['cooldown'], 0)
        self.assertEqual(train_2['cooldown'], 0)

        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()

        for i in range(town['train_cooldown']):
            map_data = self.get_map(1)
            self.assertEqual(map_data['train'][0]['cooldown'], town['train_cooldown'] - i)
            self.assertEqual(map_data['train'][1]['cooldown'], town['train_cooldown'] - i)
            self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.BAD_COMMAND)
            self.move_train(test_line_idx, train_2['idx'], 1, exp_result=Result.BAD_COMMAND)
            self.turn()
        else:
            map_data = self.get_map(1)
            self.assertEqual(map_data['train'][0]['cooldown'], 0)
            self.assertEqual(map_data['train'][1]['cooldown'], 0)
            self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.OKEY)
            self.move_train(test_line_idx, train_2['idx'], 1, exp_result=Result.OKEY)
