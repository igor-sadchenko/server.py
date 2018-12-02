""" Tests for action 'GAMES'.
"""

from attrdict import AttrDict

from server.db import map_db
from server.entity.game import GameState
from tests.lib.base_test import BaseTest
from tests.lib.server_connection import ServerConnection


class TestGameList(BaseTest):

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

    def test_game_with_init_state(self):
        game_name = self.id()
        num_players = 2
        num_turns = 100

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)

        self.login(
            name=self.players[1].name,
            game=game_name,
            num_players=num_players,
            num_turns=num_turns,
            connection=self.players[1].conn
        )

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 1)
        self.assertEqual(
            games['games'][0],
            {
                'name': game_name,
                'num_players': num_players,
                'num_turns': num_turns,
                'state': GameState.INIT,
            }
        )

    def test_game_with_run_state(self):
        game_name = self.id()
        num_players = 1
        num_turns = 100

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)

        self.login(
            name=self.players[1].name,
            game=game_name,
            num_players=num_players,
            num_turns=num_turns,
            connection=self.players[1].conn
        )

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 1)
        self.assertEqual(
            games['games'][0],
            {
                'name': game_name,
                'num_players': num_players,
                'num_turns': num_turns,
                'state': GameState.RUN,
            }
        )

    def test_game_with_finish_state(self):
        game_name = self.id()
        num_players = 1
        num_turns = 1

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)

        self.login(
            name=self.players[1].name,
            game=game_name,
            num_players=num_players,
            num_turns=num_turns,
            connection=self.players[1].conn
        )
        self.turn(connection=self.players[1].conn)

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)

    def test_game_without_players(self):
        game_name = self.id()
        num_players = 1
        num_turns = 100

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)

        self.login(
            name=self.players[1].name,
            game=game_name,
            num_players=num_players,
            num_turns=num_turns,
            connection=self.players[1].conn
        )
        self.logout(connection=self.players[1].conn)

        games = self.get_games(connection=self.players[0].conn)
        self.assertEqual(len(games['games']), 0)
