""" Tests for action LOGIN.
"""

from server.config import CONFIG
from server.db.map import DbMap
from server.defs import Result
from tests.lib.base_test import BaseTest
from tests.lib.server_connection import ServerConnection


class TestLogin(BaseTest):

    MAP_NAME = 'map02'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        DbMap().generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)

    @classmethod
    def tearDownClass(cls):
        DbMap().reset_db()
        super().tearDownClass()

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

    def test_security_key(self):
        # Second player to keep game alive after disconnect
        player_2 = 'PLAYER_2_{}_{}'.format(self.id(), self.test_start)
        player_2_conn = ServerConnection()
        num_players = 2
        self.login(
            game=self.game_name, name=player_2,
            connection=player_2_conn, num_players=num_players
        )

        security_key = 'you-will-never-guess'
        wrong_security_key = 'i-will-try-to-guess'
        self.login(
            game=self.game_name, security_key=security_key,
            num_players=num_players
        )

        self.logout()
        self.reset_connection()

        message = self.login(
            game=self.game_name, security_key=wrong_security_key,
            num_players=num_players, exp_result=Result.ACCESS_DENIED
        )
        self.assertIn('error', message)
        self.assertIn('Security key mismatch', message['error'])

        self.login(
            game=self.game_name, security_key=security_key,
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
        security_key = 'you-will-never-guess'
        wrong_security_key = 'i-will-try-to-guess'

        player_1 = self.login(security_key=security_key)
        self.reset_connection()
        message = self.login(
            game=another_game, num_players=num_players,
            security_key=wrong_security_key, exp_result=Result.ACCESS_DENIED
        )
        self.assertIn('error', message)
        self.assertIn('Security key mismatch', message['error'])
        player_2 = self.login(
            game=another_game, num_players=num_players,
            security_key=security_key
        )
        self.assertEqual(player_1, player_2)

        self.logout()
