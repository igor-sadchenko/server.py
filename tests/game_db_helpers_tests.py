""" Test DB helpers for game actions.
"""

import uuid

from sqlalchemy import and_, func

from server.db import map_db, game_db
from server.db.models import Game, Action, Player
from server.db.session import Session
from server.defs import Action as ActionCodes
from tests.lib.base_test import BaseTest


class TestGameDb(BaseTest):

    MAP_NAME = 'test01'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        map_db.generate_maps(map_names=[cls.MAP_NAME, ], active_map=cls.MAP_NAME)
        cls.map_id = map_db.get_map_by_name(cls.MAP_NAME).id

    def setUp(self):
        super().setUp()
        game_db.truncate_tables()
        self.session = Session()

    def tearDown(self):
        game_db.truncate_tables()
        self.session.close()
        super().tearDown()

    def test_add_game(self):
        num_players_1 = 1
        num_players_2 = 2
        game_name_1 = 'test_game1'
        game_name_2 = 'test_game2'

        game_db.add_game(game_name_1, self.map_id, num_players=num_players_1)
        games = self.session.query(Game).all()
        self.assertEqual(len(games), 1)
        game = games[0]
        self.assertEqual(game.name, game_name_1)
        self.assertEqual(game.map_id, self.map_id)
        self.assertEqual(game.num_players, num_players_1)

        game_db.add_game(game_name_2, self.map_id, num_players=num_players_2)
        games = self.session.query(Game).all()
        self.assertEqual(len(games), 2)
        game = games[1]
        self.assertEqual(game.name, game_name_2)
        self.assertEqual(game.map_id, self.map_id)
        self.assertEqual(game.num_players, num_players_2)

    def test_add_action(self):
        player_idx = str(uuid.uuid4())
        player_name = 'test_player'
        player_password = 'secret'
        game_db.add_player(player_idx, player_name, password=player_password)

        game_name = 'TestGame'
        game_id = game_db.add_game(game_name, self.map_id)
        code_1 = ActionCodes.LOGIN
        code_2 = ActionCodes.TURN
        message_1 = {'fake_message': 1}
        message_2 = {'fake_message': 2}

        game_db.add_action(game_id, code_1, message_1, player_idx=player_idx)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.game_id, game_id)
        self.assertEqual(action.code, code_1)
        self.assertEqual(action.message, message_1)
        self.assertEqual(action.player_id, player_idx)

        game_db.add_action(game_id, code_2, message_2, player_idx=player_idx)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 2)
        action = actions[1]
        self.assertEqual(action.game_id, game_id)
        self.assertEqual(action.code, code_2)
        self.assertEqual(action.message, message_2)
        self.assertEqual(action.player_id, player_idx)

    def test_reset_db(self):
        game_name = 'test_game'
        message = {'fake_message': 1}
        game_id = game_db.add_game(game_name, self.map_id)
        game_db.add_action(game_id, ActionCodes.LOGIN, message)

        games = self.session.query(Game).all()
        self.assertEqual(len(games), 1)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 1)

        game_db.truncate_tables()

        games = self.session.query(Game).all()
        self.assertEqual(len(games), 0)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 0)

    def test_get_all_games(self):
        length = 10
        num_players = 2
        game_name = 'test_game'
        message = {'fake_message': 1}

        game_id = game_db.add_game(game_name, self.map_id, num_players=num_players)
        game_db.add_action(game_id, ActionCodes.LOGIN, message)
        for _ in range(length):
            game_db.add_action(game_id, ActionCodes.TURN)
        game_db.add_action(game_id, ActionCodes.LOGOUT, message)

        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game1, len1 = games[0]
        game2, len2 = game_db.get_game(game_id)
        game3 = self.session.query(Game).filter(Game.id == game_id).first()
        len3 = self.session.query(func.count(Action.id)).filter(
            and_(Action.game_id == game_id, Action.code == ActionCodes.TURN.value)).scalar()

        self.assertEqual(game1, game2)
        self.assertEqual(game1, game3)
        self.assertEqual(len1, len2)
        self.assertEqual(len1, len3)

        self.assertEqual(game1.name, game_name)
        self.assertEqual(game1.map_id, self.map_id)
        self.assertEqual(game1.num_players, num_players)
        self.assertEqual(len1, length)

    def test_get_all_actions(self):
        player_idx = str(uuid.uuid4())
        player_name = 'test_player'
        player_password = 'secret'
        game_db.add_player(player_idx, player_name, password=player_password)

        game_name_1 = 'test_game1'
        game_name_2 = 'test_game2'
        code = ActionCodes.TURN
        message = {'fake_message': 1}

        game_id_1 = game_db.add_game(game_name_1, self.map_id)
        game_id_2 = game_db.add_game(game_name_2, self.map_id)

        game_db.add_action(game_id_1, code, message, player_idx=player_idx)
        game_db.add_action(game_id_2, code, message, player_idx=player_idx)

        actions = game_db.get_all_actions(game_id_1)
        self.assertEqual(len(actions), 1)
        action1 = actions[0]
        action2 = self.session.query(Action).filter(Action.game_id == game_id_1).first()
        self.assertEqual(action1, action2)

        self.assertEqual(action1.game_id, game_id_1)
        self.assertEqual(action1.code, code)
        self.assertEqual(action1.message, message)
        self.assertEqual(action1.player_id, player_idx)

        actions = game_db.get_all_actions(game_id_2)
        self.assertEqual(len(actions), 1)
        action3 = actions[0]
        action4 = self.session.query(Action).filter(Action.game_id == game_id_2).first()
        self.assertEqual(action3, action4)

        self.assertEqual(action3.game_id, game_id_2)
        self.assertEqual(action3.code, code)
        self.assertEqual(action3.message, message)
        self.assertEqual(action3.player_id, player_idx)

    def test_get_all_games_when_game_has_no_actions(self):
        length = 0
        num_players = 1
        game_name = 'test_game'
        game_id = game_db.add_game(game_name, self.map_id, num_players=num_players)

        games = game_db.get_all_games()
        self.assertEqual(len(games), 1)
        game1, len1 = games[0]
        game2 = self.session.query(Game).filter(Game.id == game_id).first()
        len2 = self.session.query(func.count(Action.id)).filter(
            and_(Action.game_id == game_id, Action.code == ActionCodes.TURN.value)).scalar()
        self.assertEqual(game1, game2)
        self.assertEqual(len1, len2)

        self.assertEqual(game1.name, game_name)
        self.assertEqual(game1.map_id, self.map_id)
        self.assertEqual(game1.num_players, num_players)
        self.assertEqual(len1, length)

    def test_add_player(self):
        idx = str(uuid.uuid4())
        name = 'test_player'
        password = 'secret'

        game_db.add_player(idx, name, password=password)
        players = self.session.query(Player).filter(Player.id == idx).all()
        self.assertEqual(len(players), 1)
        player = players[0]
        self.assertEqual(player.id, idx)
        self.assertEqual(player.name, name)
        self.assertEqual(player.password, password)

    def test_get_player(self):
        idx = str(uuid.uuid4())
        name = 'test_player'
        password = 'secret'

        game_db.add_player(idx, name, password=password)
        player = game_db.get_player_by_name(name)
        self.assertEqual(player.id, idx)
        self.assertEqual(player.name, name)
        self.assertEqual(player.password, password)
