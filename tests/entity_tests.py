""" Test server entities.
"""

import json
import unittest

from server.db.map import DbMap
from server.entity.map import Map
from server.entity.player import Player
from server.entity.point import Point
from server.entity.post import Post, PostType
from server.entity.train import Train


class TestEntity(unittest.TestCase):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        DbMap().generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        DbMap().reset_db()

    def test_map_init(self):
        """ Test create map entity.
        """
        game_map = Map(self.MAP_NAME)
        train = Train(idx=1, line_idx=game_map.lines[1].idx, position=0)
        game_map.add_train(train)

        self.assertTrue(game_map.initialized)
        self.assertEqual(len(game_map.lines), 18)
        self.assertEqual(len(game_map.points), 12)
        self.assertNotEqual(game_map.size, (None, None))
        self.assertEqual(len(game_map.coordinates), len(game_map.points))
        self.assertEqual(len(game_map.posts), 6)
        self.assertEqual(len(game_map.trains), 1)

    def test_map_serialization(self):
        """ Test Map entity serialization/deserialization.
        """
        game_map = Map(self.MAP_NAME)
        train = Train(idx=1, line_idx=game_map.lines[1].idx, position=0)
        game_map.add_train(train)

        str_json = game_map.layer_to_json_str(0)
        data = json.loads(str_json)
        self.assertIn('name', data)
        self.assertIn('lines', data)
        self.assertIn('points', data)
        self.assertIn('idx', data)
        self.assertNotIn('posts', data)
        self.assertNotIn('trains', data)
        self.assertNotIn('ratings', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinates', data)

        str_json = game_map.layer_to_json_str(1)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('lines', data)
        self.assertNotIn('points', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinates', data)
        self.assertIn('idx', data)
        self.assertIn('posts', data)
        self.assertIn('trains', data)
        self.assertIn('ratings', data)

        str_json = game_map.layer_to_json_str(10)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('lines', data)
        self.assertNotIn('points', data)
        self.assertNotIn('posts', data)
        self.assertNotIn('trains', data)
        self.assertNotIn('ratings', data)
        self.assertIn('idx', data)
        self.assertIn('size', data)
        self.assertIn('coordinates', data)

    def test_player_init(self):
        """ Test create player entity.
        """
        player_name = 'Vasya'
        player = Player.create(player_name)
        train = Train(idx=1, line_idx=1, position=0)
        point = Point(idx=1, post_idx=1)
        post = Post(idx=1, name='test-post', post_type=PostType.TOWN, point_idx=point.idx)

        player.set_home(point, post)
        player.add_train(train)

        self.assertNotEqual(player.idx, None)
        self.assertEqual(player.name, player_name)
        self.assertIn(train.idx, player.trains)
        self.assertEqual(player.trains[train.idx].player_idx, player.idx)
        self.assertIs(player.home, point)
        self.assertIs(player.town, post)

        new_player = Player.create(player_name)
        self.assertEqual(player.idx, new_player.idx)
