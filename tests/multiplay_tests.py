""" Multiplay scenarios test cases.
"""

from time import time

from attrdict import AttrDict

from server.config import CONFIG
from server.db import map_db
from server.defs import Result
from server.entity.event import Event, EventType
from tests.lib.base_test import BaseTest
from tests.lib.server_connection import ServerConnection


class TestMultiplay(BaseTest):

    MAP_NAME = 'map04'
    NUM_TOWNS = 4

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        map_db.generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    def setUp(self):
        super().setUp()
        self.players = []
        for i in range(self.NUM_TOWNS):
            player_name = 'test_player_{}_{}_{}'.format(i, self.id(), self.test_start)
            conn = ServerConnection()
            player = AttrDict({'name': player_name, 'conn': conn})
            self.players.append(player)

    def tearDown(self):
        for player in self.players:
            player.conn.close()
        super().tearDown()

    def login(self, name=None, game=None, password=None, num_players=None, exp_result=Result.OKEY, **kwargs):
        num_players = self.NUM_TOWNS if num_players is None else num_players
        game = self.game_name if game is None else game
        return super().login(
            name=name, game=game, password=password, num_players=num_players,
            exp_result=exp_result, **kwargs
        )

    def players_turn(self, players=(), turns_count=1, exp_result=Result.OKEY):
        connections = [p.conn for p in players]
        return super().players_turn(connections=connections, turns_count=turns_count, exp_result=exp_result)

    def test_login_and_logout(self):
        """ Test login and logout.
        """
        for player in self.players[:self.NUM_TOWNS]:
            self.login(player.name, connection=player.conn)
        for player in self.players[:self.NUM_TOWNS]:
            self.logout(connection=player.conn)

    def test_login_and_turn(self):
        """ Test login one by one and forced turn.
        """
        turns_num = 5
        players_in_game = 2

        self.login(self.players[0].name, num_players=players_in_game, connection=self.players[0].conn)
        self.turn(exp_result=Result.INAPPROPRIATE_GAME_STATE, connection=self.players[0].conn)
        self.login(self.players[1].name, num_players=players_in_game, connection=self.players[1].conn)
        start = time()
        self.turn(exp_result=Result.OKEY, connection=self.players[0].conn)  # Waiting for game tick.
        elapsed = time() - start
        self.assertGreater(elapsed, CONFIG.TICK_TIME / 2.0)

        for _ in range(turns_num):
            start = time()
            self.turn_no_resp(self.players[0].conn)
            self.turn_no_resp(self.players[1].conn)
            self.turn_check_resp(self.players[0].conn)
            self.turn_check_resp(self.players[1].conn)
            elapsed = time() - start
            # Ensure that game tick has been forced by players:
            self.assertLess(elapsed, CONFIG.MAX_TICK_CALCULATION_TIME)

        self.logout(connection=self.players[1].conn)
        with self.assertRaises(ConnectionError):
            self.turn(connection=self.players[1].conn)
        start = time()
        self.turn(exp_result=Result.OKEY, connection=self.players[0].conn)  # Waiting for game tick.
        elapsed = time() - start
        self.assertGreater(elapsed, CONFIG.TICK_TIME / 2.0)
        self.logout(connection=self.players[0].conn)

    def test_players_number(self):
        """ Test login with incorrect 'num_players' value and players overflow.
        """
        players_in_game = 2

        message = self.login(self.players[0].name, num_players=self.NUM_TOWNS + 1,
                             exp_result=Result.BAD_COMMAND, connection=self.players[0].conn)
        self.assertIn('error', message)
        self.assertIn('Unable to create game', message['error'])

        self.login(self.players[0].name, num_players=players_in_game, connection=self.players[0].conn)

        self.login(self.players[1].name, num_players=players_in_game + 1,
                   exp_result=Result.OKEY, connection=self.players[1].conn)

        message = self.login(self.players[2].name, num_players=players_in_game,
                             exp_result=Result.ACCESS_DENIED, connection=self.players[2].conn)
        self.assertIn('error', message)
        self.assertIn('The maximum number of players reached', message['error'])

    def test_move_train_owned_by_other_player(self):
        """ Test movements of train which is owned by other player.
        """
        players_in_game = 2
        player0 = AttrDict(
            self.login(self.players[0].name, connection=self.players[0].conn, num_players=players_in_game)
        )
        player1 = AttrDict(
            self.login(self.players[1].name, connection=self.players[1].conn, num_players=players_in_game)
        )

        # Move my train:
        valid_line = 1
        self.move_train(valid_line, player0.trains[0].idx, 1, connection=self.players[0].conn)
        # Move foreign train:
        valid_line = 19
        message = self.move_train(valid_line, player1.trains[0].idx, -1,
                                  exp_result=Result.ACCESS_DENIED, connection=self.players[0].conn)
        self.assertIn('error', message)
        self.assertIn('Train\'s owner mismatch', message['error'])

    def test_train_unload_in_foreign_town(self):
        """ Test train unload in foreign town.
        """
        players_in_game = 2

        player0 = AttrDict(self.login(self.players[0].name, num_players=players_in_game,
                                      connection=self.players[0].conn))
        self.login(self.players[1].name, num_players=players_in_game, connection=self.players[1].conn)

        # Path to Market:
        path = [
            (10, 1, 5),
            (29, 1, 5),
            (48, 1, 5),
            (58, 1, 4),
            (59, 1, 4),
            (60, 1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, player0.trains[0].idx, speed, connection=self.players[0].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        train_before = AttrDict(self.get_train(player0.trains[0].idx, connection=self.players[0].conn))

        # Path to foreign Town:
        path = [
            (51, -1, 5),
            (32, -1, 5),
            (13, -1, 5),
            (4, 1, 4),
            (5, 1, 4),
            (6, 1, 4),
            (7, 1, 4),
            (8, 1, 4),
            (9, 1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, player0.trains[0].idx, speed, connection=self.players[0].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        train_after = AttrDict(self.get_train(player0.trains[0].idx, connection=self.players[0].conn))

        self.assertGreater(train_before.goods, 0)
        self.assertEqual(train_before.goods, train_after.goods)

    def test_upgrade_train_owned_by_other_player(self):
        """ Test upgrade of train which is owned by other player.
        """
        players_in_game = 2

        player0 = AttrDict(self.login(self.players[0].name, num_players=players_in_game,
                                      connection=self.players[0].conn))
        player1 = AttrDict(self.login(self.players[1].name, num_players=players_in_game,
                                      connection=self.players[1].conn))
        town0 = AttrDict(self.get_post(player0.town.idx, connection=self.players[0].conn))
        town1 = AttrDict(self.get_post(player1.town.idx, connection=self.players[1].conn))
        train0 = AttrDict(self.get_train(player0.trains[0].idx, connection=self.players[0].conn))
        train1 = AttrDict(self.get_train(player1.trains[0].idx, connection=self.players[1].conn))

        # Mine armor for 1-st player:
        # Path to Storage:
        path = [
            (10, 1, 5),
            (29, 1, 5),
            (48, 1, 5),
            (67, 1, 5),
            (77, 1, 4),
            (78, 1, 4),
            (79, 1, 4),
            (80, 1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, train0.idx, speed, connection=self.players[0].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)
        else:
            # Wait for replenishment:
            turns_to_get_full_train = 4
            self.players_turn(self.players[:players_in_game], turns_count=turns_to_get_full_train)
        for line_idx, speed, length in reversed(path):
            self.move_train(line_idx, train0.idx, -1 * speed, connection=self.players[0].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        town0_after = AttrDict(self.get_post(player0.town.idx, connection=self.players[0].conn))
        self.assertEqual(town0_after.armor, town0.armor + train0.goods_capacity)

        # Mine armor for 2-nd player:
        # Path to Storage:
        path = [
            (19, 1, 5),
            (38, 1, 5),
            (57, 1, 5),
            (76, 1, 5),
            (85, -1, 4),
            (84, -1, 4),
            (83, -1, 4),
            (82, -1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, train1.idx, speed, connection=self.players[1].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)
        else:
            # Wait for replenishment:
            turns_to_get_full_train = 4
            self.players_turn(self.players[:players_in_game], turns_count=turns_to_get_full_train)
        for line_idx, speed, length in reversed(path):
            self.move_train(line_idx, train1.idx, -1 * speed, connection=self.players[1].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        town1_after = AttrDict(self.get_post(player1.town.idx, connection=self.players[1].conn))
        self.assertEqual(town1_after.armor, town1.armor + train1.goods_capacity)

        # Upgrade foreign train:
        message = self.upgrade(trains=[train1.idx], exp_result=Result.ACCESS_DENIED, connection=self.players[0].conn)
        self.assertIn('error', message)
        self.assertIn('Train\'s owner mismatch', message['error'])
        message = self.upgrade(trains=[train0.idx], exp_result=Result.ACCESS_DENIED, connection=self.players[1].conn)
        self.assertIn('error', message)
        self.assertIn('Train\'s owner mismatch', message['error'])

        # Upgrade not foreign train:
        self.upgrade(trains=[train0.idx], connection=self.players[0].conn)
        self.upgrade(trains=[train1.idx], connection=self.players[1].conn)

    def test_user_events(self):
        """ Test users events independence.
        """
        players_in_game = 2

        player0 = AttrDict(self.login(self.players[0].name, num_players=players_in_game,
                                      connection=self.players[0].conn))
        player1 = AttrDict(self.login(self.players[1].name, num_players=players_in_game,
                                      connection=self.players[1].conn))
        train0 = AttrDict(self.get_train(player0.trains[0].idx, connection=self.players[0].conn))
        train1 = AttrDict(self.get_train(player1.trains[0].idx, connection=self.players[1].conn))

        # Path to collision for 1-st train:
        path = [
            (1, 1, 4),
            (2, 1, 4),
            (3, 1, 4),
            (4, 1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, train0.idx, speed, connection=self.players[0].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        # Path to collision for 2-nd train:
        path = [
            (9, -1, 4),
            (8, -1, 4),
            (7, -1, 4),
            (6, -1, 4),
            (5, -1, 4),
        ]
        for line_idx, speed, length in path:
            self.move_train(line_idx, train1.idx, speed, connection=self.players[1].conn)
            self.players_turn(self.players[:players_in_game], turns_count=length)

        train0_after = AttrDict(self.get_train(player0.trains[0].idx, connection=self.players[0].conn))
        self.assertTrue(
            self.check_collision_event(
                train0_after.events,
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train1.idx)
            )
        )
        self.assertEqual(train0_after.line_idx, train0.line_idx)
        self.assertEqual(train0_after.position, train0.position)

        train1_after = AttrDict(self.get_train(player1.trains[0].idx, connection=self.players[1].conn))
        self.assertTrue(
            self.check_collision_event(
                train1_after.events,
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train0.idx)
            )
        )
        self.assertEqual(train1_after.line_idx, train1.line_idx)
        self.assertEqual(train1_after.position, train1.position)

    def test_four_players(self):
        """ Test with 4 players.
        """
        players_in_game = 4

        player0 = AttrDict(self.login(self.players[0].name, num_players=players_in_game,
                                      connection=self.players[0].conn))
        player1 = AttrDict(self.login(self.players[1].name, num_players=players_in_game,
                                      connection=self.players[1].conn))
        player2 = AttrDict(self.login(self.players[2].name, num_players=players_in_game,
                                      connection=self.players[2].conn))
        player3 = AttrDict(self.login(self.players[3].name, num_players=players_in_game,
                                      connection=self.players[3].conn))

        line_path = (
            [1, 19, 162, 180],
            [2, 38, 143, 179],
            [3, 57, 124, 178],
            [4, 76, 105, 177],
            [5, 95, 86, 176],
            [6, 114, 67, 175],
            [7, 133, 48, 174],
            [8, 152, 29, 173],
            [9, 171, 10, 172]
        )

        for lines in line_path:
            self.move_train(lines[0], player0.trains[0].idx, 1, connection=self.players[0].conn)
            self.move_train(lines[1], player1.trains[0].idx, 1, connection=self.players[1].conn)
            self.move_train(lines[2], player2.trains[0].idx, -1, connection=self.players[2].conn)
            self.move_train(lines[3], player3.trains[0].idx, -1, connection=self.players[3].conn)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        for i in range(players_in_game):
            self.logout(connection=self.players[i].conn)
