""" Tests for action LOGIN.
"""

from server.config import CONFIG
from server.db import map_db
from server.defs import Result
from tests.lib.base_test import BaseTest
from tests.lib.server_connection import ServerConnection


class TestLogin(BaseTest):

    MAP_NAME = 'test01'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        map_db.generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    def test_repeat_login(self):
        self.login()
        message = self.login(exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('You are already logged in', message['error'])
        self.logout()

    def test_login_to_another_game(self):
        another_game = 'ANOTHER_GAME_NAME'
        self.login()
        message = self.login(game=another_game, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn('You are already logged in', message['error'])
        self.logout()

    def test_password(self):
        # Second player to keep game alive after disconnect
        player_2 = 'PLAYER_2_{}_{}'.format(self.id(), self.test_start)
        player_2_conn = ServerConnection()
        num_players = 2
        self.login(
            game=self.game_name, name=player_2,
            connection=player_2_conn, num_players=num_players
        )

        password = 'you-will-never-guess'
        wrong_password = 'i-will-try-to-guess'
        self.login(
            game=self.game_name, password=password,
            num_players=num_players
        )

        self.logout()
        self.reset_connection()

        message = self.login(
            game=self.game_name, password=wrong_password,
            num_players=num_players, exp_result=Result.ACCESS_DENIED
        )
        self.assertIn('error', message)
        self.assertIn('Password mismatch', message['error'])

        self.login(
            game=self.game_name, password=password,
            num_players=num_players
        )
        self.logout()
        self.logout(connection=player_2_conn)
        player_2_conn.close()

    def test_player_action(self):
        login = self.login()
        player = self.get_player()
        self.assertEqual(player, login)
        self.logout()

    def test_disconnect_and_login_to_the_same_game(self):
        # Second player to keep game alive after disconnect
        player_2 = 'PLAYER_2_{}_{}'.format(self.id(), self.test_start)
        player_2_conn = ServerConnection()
        num_players = 2

        self.login(game=self.game_name, name=player_2, connection=player_2_conn, num_players=num_players)
        self.login(game=self.game_name, num_players=num_players)
        self.players_turn([self.connection, player_2_conn])
        player_before_disconnect = self.get_player()

        # Disconnect
        self.reset_connection()

        player_after_disconnect = self.login(game=self.game_name, num_players=num_players)
        self.assertEqual(player_before_disconnect, player_after_disconnect)

        self.logout()
        self.logout(connection=player_2_conn)
        player_2_conn.close()

    def test_reuse_player_name(self):
        # Second player
        player_2 = 'PLAYER_2_{}_{}'.format(self.id(), self.test_start)
        player_2_conn = ServerConnection()
        num_players = 2

        self.login(game=self.game_name, name=player_2, connection=player_2_conn, num_players=num_players)
        self.login(game=self.game_name, num_players=num_players)
        self.players_turn([self.connection, player_2_conn])

        self.logout()
        self.reset_connection()
        self.logout(connection=player_2_conn)
        player_2_conn.close()

        player = self.login()
        self.assertEqual(player['rating'], 0)
        self.assertEqual(len(player['trains']), CONFIG.TRAINS_COUNT)

    def test_disconnect_and_login_to_another_game(self):
        another_game = 'ANOTHER_GAME_NAME'
        num_players = 1
        password = 'you-will-never-guess'
        wrong_password = 'i-will-try-to-guess'

        player_1 = self.login(password=password)
        self.reset_connection()
        message = self.login(
            game=another_game, num_players=num_players,
            password=wrong_password, exp_result=Result.ACCESS_DENIED
        )
        self.assertIn('error', message)
        self.assertIn('Password mismatch', message['error'])
        player_2 = self.login(
            game=another_game, num_players=num_players,
            password=password
        )
        self.assertEqual(player_1, player_2)

        self.logout()

    def test_one_username_two_connections_different_games(self):
        conn1 = ServerConnection()
        conn2 = ServerConnection()
        game_name_1 = 'GAME_1_{}_{}'.format(self.id(), self.test_start)
        game_name_2 = 'GAME_2_{}_{}'.format(self.id(), self.test_start)

        player1 = self.login(name=self.player_name, game=game_name_1, num_players=1, connection=conn1)
        player2 = self.login(name=self.player_name, game=game_name_2, num_players=1, connection=conn2)

        self.assertEqual(len(player1['trains']), CONFIG.TRAINS_COUNT)
        self.assertEqual(len(player2['trains']), CONFIG.TRAINS_COUNT)

        self.move_train(1, player1['trains'][0]['idx'], 1, connection=conn1)
        self.turn(connection=conn1)

        player1 = self.get_player(connection=conn1)
        player2 = self.get_player(connection=conn2)

        self.assertEqual(player1['trains'][0]['line_idx'], 1)
        self.assertEqual(player1['trains'][0]['position'], 1)
        self.assertEqual(player1['rating'], 3060)

        self.assertEqual(player2['trains'][0]['line_idx'], 1)
        self.assertEqual(player2['trains'][0]['position'], 0)
        self.assertEqual(player2['rating'], 0)

        conn1.close()
        conn2.close()

    def test_one_username_two_connections_one_game(self):
        conn1 = ServerConnection()
        conn2 = ServerConnection()

        player1 = self.login(name=self.player_name, game=self.game_name, num_players=1, connection=conn1)
        player2 = self.login(name=self.player_name, game=self.game_name, num_players=1, connection=conn2)

        self.assertEqual(player1, player2)

        self.move_train(1, player1['trains'][0]['idx'], 1, connection=conn1)
        self.turn(connection=conn1)
        self.players_turn(connections=(conn1, conn2, ))

        player1 = self.get_player(connection=conn1)
        player2 = self.get_player(connection=conn2)

        self.assertEqual(player1, player2)

        conn1.close()
        conn2.close()
