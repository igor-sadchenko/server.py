""" Game entity.
"""
import math
import random
from enum import IntEnum
from threading import Thread, Event, Lock, Condition

import errors
from config import CONFIG
from db import game_db
from defs import Action
from entity.event import EventType, Event as GameEvent
from entity.map import Map
from entity.player import Player
from entity.point import Point
from entity.post import PostType, Post
from entity.train import Train
from logger import log


class GameState(IntEnum):
    """ Game states.
    """
    INIT = 1
    RUN = 2
    FINISHED = 3


class Game(Thread):

    GAMES = {}  # All registered games.

    def __init__(self, name, observed=False, num_players=1, map_name=None):
        super(Game, self).__init__(name=name)
        log.info('Create game, name: \'{}\''.format(self.name))
        self.name = name
        self.state = GameState.INIT
        self.current_tick = 0
        self.observed = observed
        self.num_players = num_players
        self.map = Map(use_active=True) if map_name is None else Map(name=map_name)
        if self.num_players > len(self.map.towns):
            raise errors.BadCommand(
                'Unable to create game with {} players, maximum players count is {}'.format(
                    self.num_players, len(self.map.towns))
            )
        if self.observed:
            self.game_idx = 0
        else:
            self.game_idx = game_db.add_game(name, self.map.idx, num_players=num_players)
        self.players = {}
        self.trains = {}
        self.next_train_moves = {}
        self.event_cooldowns = CONFIG.EVENT_COOLDOWNS_ON_START.copy()
        self._lock = Lock()
        self._stop_event = Event()
        self._start_tick_event = Event()
        self._tick_done_condition = Condition()
        random.seed()

    @staticmethod
    def get(name, **kwargs):
        """ Returns instance of class Game.
        """
        if name in Game.GAMES:
            game = Game.GAMES[name]
        else:
            Game.GAMES[name] = game = Game(name, **kwargs)
        return game

    @staticmethod
    def stop_all_games():
        """ Stops all games. Uses on server shutdown.
        """
        for game_name in list(Game.GAMES.keys()):
            Game.GAMES.pop(game_name).stop()

    def add_player(self, player: Player):
        """ Adds player to the game.
        """
        # Check game state:
        if self.state == GameState.FINISHED:
            raise errors.AccessDenied('The game is finished')

        # If player is returning to the game:
        if player.idx in self.players:
            player = self.players[player.idx]
            player.in_game = True
            return player

        # Add new player to the game:
        with self._lock:

            # Check players count:
            if len(self.players) == self.num_players:
                raise errors.AccessDenied('The maximum number of players reached')
            else:
                self.players[player.idx] = player
                player.in_game = True

            # Pick first available Town on the map as player's Town:
            player_town = [t for t in self.map.towns if t.player_idx is None][0]
            player_home_point = self.map.points[player_town.point_idx]
            player.set_home(player_home_point, player_town)

            # Create trains for the player:
            start_train_idx = len(self.trains) + 1
            for i in range(CONFIG.TRAINS_COUNT):
                # Create Train:
                train = Train(idx=start_train_idx + i)
                # Add Train:
                player.add_train(train)
                self.map.add_train(train)
                self.trains[train.idx] = train
                # Put the Train into Town:
                self.put_train_into_town(train, with_cooldown=False)

        # Set player's rating:
        self.map.ratings[player.idx] = {
            'rating': player.rating,
            'name': player.name,
            'idx': player.idx
        }

        log.info('Add new player to the game, player: {}'.format(player))

        # Start thread with game loop:
        self.start()

        return player

    def remove_player(self, player: Player):
        """ Removes player from the game.
        """
        player.in_game = False
        self.stop_if_no_players()

    def turn(self, player: Player):
        """ Makes next turn.
        """
        if self.state != GameState.RUN:
            raise errors.NotReady('Game state is not \'RUN\', state: {}'.format(self.state))
        with self._tick_done_condition:
            with self._lock:
                player.turn_called = True
                all_ready_for_turn = all([p.turn_called for p in self.players.values()])
                if all_ready_for_turn:
                    self._start_tick_event.set()
            if not self._tick_done_condition.wait(CONFIG.TURN_TIMEOUT):
                raise errors.Timeout('Game tick did not happen')

    def start(self):
        """ Starts game ticks (game loop).
        """
        if self.num_players == len(self.players) and self.state == GameState.INIT:
            log.info('Game started, name: \'{}\''.format(self.name))
            self.state = GameState.RUN
            if not self.observed:
                super().start()

    def stop(self):
        """ Stops game ticks (game loop).
        """
        if self.state != GameState.FINISHED:
            log.info('Game stopped, name: \'{}\''.format(self.name))
            self.state = GameState.FINISHED
            self._stop_event.set()
            if self.name in Game.GAMES:
                Game.GAMES.pop(self.name)

    def stop_if_no_players(self):
        """ Stops the game if there are no 'in_game' players.
        """
        if not any([p.in_game for p in self.players.values()]):
            self.stop()

    def run(self):
        """ Thread's activity. The loop with game ticks.
        """
        while not self._stop_event.is_set():
            self._start_tick_event.wait(CONFIG.TICK_TIME)
            with self._lock and self._tick_done_condition:
                if self.state != GameState.RUN:
                    break  # Finish game thread.
                try:
                    self.tick()
                except Exception:
                    log.exception('Got unhandled exception on tick, game id: {}'.format(self.game_idx))
                    raise
                if self._start_tick_event.is_set():
                    self._start_tick_event.clear()
                for player in self.players.values():
                    player.turn_called = False
                self._tick_done_condition.notify_all()

    def tick(self):
        """ Makes game tick. Updates dynamic game entities.
        """
        self.current_tick += 1
        log.info('Game tick, tick number: {}, game id: {}'.format(self.current_tick, self.game_idx))

        # Turn steps:
        self.update_cooldowns_on_tick()  # Update cooldowns in the beginning of the tick.
        self.update_posts_on_tick()
        self.update_trains_positions_on_tick()
        self.handle_trains_collisions_on_tick()
        self.process_trains_points_on_tick()
        self.update_towns_on_tick()
        self.refugees_arrival_on_tick()
        self.hijackers_assault_on_tick()
        self.parasites_assault_on_tick()
        self.recalculate_ratings_on_tick()
        self.retire_events_on_tick()

        if not self.observed:
            game_db.add_action(self.game_idx, Action.TURN)

    def train_in_point(self, train: Train, point_idx: int):
        """ Makes all needed actions when Train arrives to Point.
        Applies next Train move if it exist, processes Post if exist in the Point.
        """
        msg = 'Train is in point, train: {}, point: {}'.format(train, self.map.points[point_idx])

        post_idx = self.map.points[point_idx].post_idx
        if post_idx is not None:
            msg += ", post: {!r}".format(self.map.posts[post_idx].type)
            self.train_in_post(train, self.map.posts[post_idx])

        log.debug(msg)

        self.apply_next_train_move(train)

    def apply_next_train_move(self, train: Train):
        """ Applies postponed Train MOVE if it exist.
        """
        if train.idx in self.next_train_moves:
            next_move = self.next_train_moves[train.idx]
            # If next line the same as previous:
            # TODO: This case is not possible?
            if next_move['line_idx'] == train.line_idx:
                if train.speed > 0 and train.position == self.map.lines[train.line_idx].length:
                    train.speed = 0
                elif train.speed < 0 and train.position == 0:
                    train.speed = 0
            # If next line differs from previous:
            else:
                train.speed = next_move['speed']
                train.line_idx = next_move['line_idx']
                if train.speed > 0:
                    train.position = 0
                elif train.speed < 0:
                    train.position = self.map.lines[train.line_idx].length
        # The train hasn't got next move data, stop the train.
        else:
            train.speed = 0

    def move_train(self, player, train_idx, speed, line_idx):
        """ Process action MOVE. Changes path or speed of the Train.
        """
        with self._lock:
            if train_idx not in self.trains:
                raise errors.ResourceNotFound('Train index not found, index: {}'.format(train_idx))
            if line_idx not in self.map.lines:
                raise errors.ResourceNotFound('Line index not found, index: {}'.format(line_idx))
            train = self.trains[train_idx]
            if train.player_idx != player.idx:
                raise errors.AccessDenied('Train\'s owner mismatch')
            if train_idx in self.next_train_moves:
                self.next_train_moves.pop(train_idx)

            # Check cooldown for the train:
            if train.cooldown > 0:
                raise errors.BadCommand('The train is under cooldown, cooldown: {}'.format(train.cooldown))

            # Stop the train; reverse direction on move; continue run the train:
            if speed == 0 or train.line_idx == line_idx:
                train.speed = speed

            # The train is standing:
            elif train.speed == 0:
                # The train is standing at the end of the line:
                if self.map.lines[train.line_idx].length == train.position:
                    line_from = self.map.lines[train.line_idx]
                    line_to = self.map.lines[line_idx]
                    if line_from.points[1] in line_to.points:
                        train.line_idx = line_idx
                        train.speed = speed
                        if line_from.points[1] == line_to.points[0]:
                            train.position = 0
                        else:
                            train.position = line_to.length
                    else:
                        raise errors.BadCommand(
                            'The end of the train\'s line is not connected to the next line, '
                            'train\'s line: {}, next line: {}'.format(line_from, line_to)
                        )
                # The train is standing at the beginning of the line:
                elif train.position == 0:
                    line_from = self.map.lines[train.line_idx]
                    line_to = self.map.lines[line_idx]
                    if line_from.points[0] in line_to.points:
                        train.line_idx = line_idx
                        train.speed = speed
                        if line_from.points[0] == line_to.points[0]:
                            train.position = 0
                        else:
                            train.position = line_to.length
                    else:
                        raise errors.BadCommand(
                            'The beginning of the train\'s line is not connected to the next line, '
                            'train\'s line: {}, next line: {}'.format(line_from, line_to)
                        )
                # The train is standing on the line (between line's points), player have to continue run the train.
                else:
                    raise errors.BadCommand(
                        'The train is standing on the line (between line\'s points), '
                        'player have to continue run the train'
                    )

            # The train is moving on the line (between line's points):
            elif train.speed != 0 and train.line_idx != line_idx:
                switch_line_possible = False
                line_from = self.map.lines[train.line_idx]
                line_to = self.map.lines[line_idx]
                if train.speed > 0 and speed > 0:
                    switch_line_possible = (line_from.points[1] == line_to.points[0])
                elif train.speed > 0 and speed < 0:
                    switch_line_possible = (line_from.points[1] == line_to.points[1])
                elif train.speed < 0 and speed > 0:
                    switch_line_possible = (line_from.points[0] == line_to.points[0])
                elif train.speed < 0 and speed < 0:
                    switch_line_possible = (line_from.points[0] == line_to.points[1])

                # This train move request is valid and will be applied later:
                if switch_line_possible:
                    self.next_train_moves[train_idx] = {'speed': speed, 'line_idx': line_idx}
                # This train move request is invalid:
                else:
                    raise errors.BadCommand(
                        'The train is not able to switch the current line to the next line, '
                        'or new speed is incorrect, train\'s line: {}, next line: {}, '
                        'train\'s speed: {}, new speed: {}'.format(line_from, line_to, train.speed, speed)
                    )

    def train_in_post(self, train: Train, post: Post):
        """ Makes all needed actions when Train arrives to Post.
        Behavior depends on PostType, train can be loaded or unloaded.
        """
        if post.type == PostType.TOWN and train.player_idx == post.player_idx:
            # Unload product from train to town:
            goods = 0
            if train.goods_type == PostType.MARKET:
                goods = max(min(train.goods, post.product_capacity - post.product), 0)
                post.product += goods
                if post.product >= post.product_capacity:
                    post.events.append(GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, product=post.product))
            elif train.goods_type == PostType.STORAGE:
                goods = max(min(train.goods, post.armor_capacity - post.armor), 0)
                post.armor += goods
                if post.armor >= post.armor_capacity:
                    post.events.append(GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, armor=post.armor))

            if CONFIG.TRAIN_ALWAYS_DEVASTATED:
                train.goods = 0
            else:
                train.goods -= goods
            if train.goods == 0:
                train.goods_type = None

            # Fill up trains's tank:
            train.fuel = train.fuel_capacity

        elif post.type == PostType.MARKET:
            # Load product from market to train:
            if train.goods_type is None or train.goods_type == post.type:
                product = max(min(post.product, train.goods_capacity - train.goods), 0)
                post.product -= product
                train.goods += product
                train.goods_type = post.type

        elif post.type == PostType.STORAGE:
            # Load armor from storage to train:
            if train.goods_type is None or train.goods_type == post.type:
                armor = max(min(post.armor, train.goods_capacity - train.goods), 0)
                post.armor -= armor
                train.goods += armor
                train.goods_type = post.type

    def put_train_into_town(self, train: Train, with_unload=True, with_cooldown=True):
        """ Puts given Train to his Town.
        """
        # Get Train owner's home point:
        player_home_point = self.players[train.player_idx].home
        # Use first Line connected to the home point as default train's line:
        line = [l for l in self.map.lines.values() if player_home_point.idx in l.points][0]
        train.line_idx = line.idx
        # Set Train's position at the Town:
        if player_home_point.idx == line.points[0]:
            train.position = 0
        else:
            train.position = line.length
        # Stop Train:
        train.speed = 0
        # Unload the Train:
        if with_unload:
            train.goods = 0
            train.goods_type = None
        # Set cooldown for the Train:
        if with_cooldown:
            # Get Train owner's town:
            player_town = self.players[train.player_idx].town
            train.cooldown = player_town.train_cooldown

    def make_hijackers_assault(self, hijackers_power):
        """ Makes hijackers assault which decreases quantity of Town's armor and population.
        """
        log.info('Hijackers assault happened, hijackers power: {}'.format(hijackers_power))
        event = GameEvent(EventType.HIJACKERS_ASSAULT, self.current_tick, hijackers_power=hijackers_power)
        for player in self.players.values():
            player.town.population = max(player.town.population - max(hijackers_power - player.town.armor, 0), 0)
            player.town.armor = max(player.town.armor - hijackers_power, 0)
            player.town.events.append(event)
        self.event_cooldowns[EventType.HIJACKERS_ASSAULT] = round(
            hijackers_power * CONFIG.HIJACKERS_COOLDOWN_COEFFICIENT)
        if not self.observed:
            game_db.add_action(self.game_idx, Action.EVENT, event.to_dict())

    def hijackers_assault_on_tick(self):
        """ Makes randomly hijackers assault if it is possible.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.HIJACKERS_ASSAULT, 0) > 0 or self.observed:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= CONFIG.HIJACKERS_ASSAULT_PROBABILITY:
            hijackers_power = random.randint(*CONFIG.HIJACKERS_POWER_RANGE)
            self.make_hijackers_assault(hijackers_power)

    def make_parasites_assault(self, parasites_power):
        """ Makes parasites assault which decreases quantity of Town's product.
        """
        log.info('Parasites assault happened, parasites power: {}'.format(parasites_power))
        event = GameEvent(EventType.PARASITES_ASSAULT, self.current_tick, parasites_power=parasites_power)
        for player in self.players.values():
            player.town.product = max(player.town.product - parasites_power, 0)
            player.town.events.append(event)
        self.event_cooldowns[EventType.PARASITES_ASSAULT] = round(
            parasites_power * CONFIG.PARASITES_COOLDOWN_COEFFICIENT)
        if not self.observed:
            game_db.add_action(self.game_idx, Action.EVENT, event.to_dict())

    def parasites_assault_on_tick(self):
        """ Makes randomly parasites assault if it is possible.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.PARASITES_ASSAULT, 0) > 0 or self.observed:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= CONFIG.PARASITES_ASSAULT_PROBABILITY:
            parasites_power = random.randint(*CONFIG.PARASITES_POWER_RANGE)
            self.make_parasites_assault(parasites_power)

    def make_refugees_arrival(self, refugees_number):
        """ Makes refugees arrival which increases quantity of Town's population.
        """
        log.info('Refugees arrival happened, refugees number: {}'.format(refugees_number))
        event = GameEvent(EventType.REFUGEES_ARRIVAL, self.current_tick, refugees_number=refugees_number)
        for player in self.players.values():
            player.town.population += max(
                min(player.town.population_capacity - player.town.population, refugees_number), 0
            )
            player.town.events.append(event)
            if player.town.population == player.town.population_capacity:
                player.town.events.append(
                    GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, population=player.town.population)
                )
        self.event_cooldowns[EventType.REFUGEES_ARRIVAL] = round(
            refugees_number * CONFIG.REFUGEES_COOLDOWN_COEFFICIENT)
        if not self.observed:
            game_db.add_action(self.game_idx, Action.EVENT, event.to_dict())

    def refugees_arrival_on_tick(self):
        """ Makes randomly refugees arrival if it is possible.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.REFUGEES_ARRIVAL, 0) > 0 or self.observed:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= CONFIG.REFUGEES_ARRIVAL_PROBABILITY:
            refugees_number = random.randint(*CONFIG.REFUGEES_NUMBER_RANGE)
            self.make_refugees_arrival(refugees_number)

    def update_posts_on_tick(self):
        """ Updates all markets and storages.
        """
        for market in self.map.markets:
            if market.product < market.product_capacity:
                market.product = max(min(market.product + market.replenishment, market.product_capacity), 0)
        for storage in self.map.storages:
            if storage.armor < storage.armor_capacity:
                storage.armor = max(min(storage.armor + storage.replenishment, storage.armor_capacity), 0)

    def update_trains_positions_on_tick(self):
        """ Update trains positions.
        """
        for train in self.trains.values():
            if CONFIG.FUEL_ENABLED and train.speed != 0:
                train.fuel -= train.fuel_consumption
                if train.fuel < 0:
                    self.put_train_into_town(train, with_unload=True, with_cooldown=True)
            line = self.map.lines[train.line_idx]
            if train.speed > 0 and train.position < line.length:
                train.position += 1
            elif train.speed < 0 and train.position > 0:
                train.position -= 1

    def process_trains_points_on_tick(self):
        """ Update trains positions, process points.
        """
        for train in self.trains.values():
            line = self.map.lines[train.line_idx]
            if train.position == line.length or train.position == 0:
                self.train_in_point(train, line.points[self.get_sign(train.position)])

    def update_towns_on_tick(self):
        """ Update population and products in Towns.
        """
        for player in self.players.values():
            if player.town.product < player.town.population:
                player.town.population = max(player.town.population - 1, 0)
            player.town.product = max(player.town.product - player.town.population, 0)
            if player.town.population == 0:
                # TODO: process game over?
                player.town.events.append(GameEvent(EventType.GAME_OVER, self.current_tick, population=0))
            if player.town.product == 0:
                player.town.events.append(GameEvent(EventType.RESOURCE_LACK, self.current_tick, product=0))
            if player.town.armor == 0:
                player.town.events.append(GameEvent(EventType.RESOURCE_LACK, self.current_tick, armor=0))

    @staticmethod
    def get_sign(variable):
        """ Returns sign of the variable.
         1 if variable >  0
        -1 if variable <  0
         0 if variable == 0
        """
        return variable and (1, -1)[variable < 0]

    def is_train_at_point(self, train: Train, point_to_check: Point = None):
        """ Returns Point if the Train at some Point now, else returns False.
        """
        line = self.map.lines[train.line_idx]
        if train.position == line.length or train.position == 0:
            point_idx = line.points[self.get_sign(train.position)]
            point = self.map.points[point_idx]
            if point_to_check is None or point_to_check.idx == point.idx:
                return point
        return False

    def is_train_at_post(self, train: Train, post_to_check: Post = None):
        """ Returns Post if the Train at some Post now, else returns False.
        """
        point = self.is_train_at_point(train)
        if point and point.post_idx:
            post = self.map.posts[point.post_idx]
            if post_to_check is None or post_to_check.idx == post.idx:
                return post
        return False

    def make_collision(self, train_1: Train, train_2: Train):
        """ Makes collision between two trains.
        """
        log.info('Trains collision happened, trains: [{}, {}]'.format(train_1, train_2))
        self.put_train_into_town(train_1, with_unload=True, with_cooldown=True)
        self.put_train_into_town(train_2, with_unload=True, with_cooldown=True)
        train_1.events.append(GameEvent(EventType.TRAIN_COLLISION, self.current_tick, train=train_2.idx))
        train_2.events.append(GameEvent(EventType.TRAIN_COLLISION, self.current_tick, train=train_1.idx))

    def handle_trains_collisions_on_tick(self):
        """ Handles Trains collisions.
        """
        if not CONFIG.COLLISIONS_ENABLED:
            return

        collision_pairs = []
        trains = list(self.trains.values())
        for i, train_1 in enumerate(trains):
            # Get Line and Point of train_1:
            line_1 = self.map.lines[train_1.line_idx]
            point_1 = self.is_train_at_point(train_1)
            for train_2 in trains[i + 1:]:
                # Get Line and Point of train_2:
                line_2 = self.map.lines[train_2.line_idx]
                point_2 = self.is_train_at_point(train_2)
                # If train_1 and train_2 at the same Point:
                if point_1 and point_2 and point_1.idx == point_2.idx:
                    post = None if point_1.post_idx is None else self.map.posts[point_1.post_idx]
                    if post is not None and post.type in {PostType.TOWN, }:
                        continue
                    else:
                        collision_pairs.append((train_1, train_2))
                        continue
                # If train_1 and train_2 on the same Line:
                if line_1.idx == line_2.idx:
                    # If train_1 and train_2 have the same position:
                    if train_1.position == train_2.position:
                        collision_pairs.append((train_1, train_2))
                        continue
                    # Skip if train_1 or train_2 has been stopped and they have different positions:
                    if train_1.speed == 0 or train_2.speed == 0:
                        continue
                    # Calculating distance between train_1 and train_2 now and after next tick:
                    train_step_1 = self.get_sign(train_1.speed)
                    train_step_2 = self.get_sign(train_2.speed)
                    dist_before_tick = math.fabs(train_1.position - train_2.position)
                    dist_after_tick = math.fabs(train_1.position + train_step_1 - train_2.position + train_step_2)
                    # If after next tick train_1 and train_2 cross:
                    if dist_before_tick == dist_after_tick == 1 and train_step_1 + train_step_2 == 0:
                        collision_pairs.append((train_1, train_2))
                        continue
        for pair in collision_pairs:
            self.make_collision(*pair)

    def make_upgrade(self, player: Player, posts_idx=(), trains_idx=()):
        """ Upgrades given Posts and Trains to next level.
        """
        with self._lock:
            # Get posts from request:
            posts = []
            for post_idx in posts_idx:
                if post_idx not in self.map.posts:
                    raise errors.ResourceNotFound('Post index not found, index: {}'.format(post_idx))
                post = self.map.posts[post_idx]
                if post.type != PostType.TOWN:
                    raise errors.BadCommand('The post is not a Town, post: {}'.format(post))
                if post.player_idx != player.idx:
                    raise errors.AccessDenied('Town\'s owner mismatch')
                posts.append(post)

            # Get trains from request:
            trains = []
            for train_idx in trains_idx:
                if train_idx not in self.trains:
                    raise errors.ResourceNotFound('Train index not found, index: {}'.format(train_idx))
                train = self.trains[train_idx]
                if train.player_idx != player.idx:
                    raise errors.AccessDenied('Train\'s owner mismatch')
                trains.append(train)

            # Check existence of next level for each entity:
            posts_has_next_lvl = all([p.level + 1 in CONFIG.TOWN_LEVELS for p in posts])
            trains_has_next_lvl = all([t.level + 1 in CONFIG.TRAIN_LEVELS for t in trains])
            if not all([posts_has_next_lvl, trains_has_next_lvl]):
                raise errors.BadCommand('Not all entities requested for upgrade have next levels')

            # Check armor quantity for upgrade:
            armor_to_up_posts = sum([p.next_level_price for p in posts])
            armor_to_up_trains = sum([t.next_level_price for t in trains])
            armor_to_up = sum([armor_to_up_posts, armor_to_up_trains])
            if player.town.armor < armor_to_up:
                raise errors.BadCommand(
                    'Not enough armor resource for upgrade, player\'s armor: {}, '
                    'armor needed to upgrade: {}'.format(player.town.armor, armor_to_up)
                )

            # Check that trains are in town now:
            for train in trains:
                if not self.is_train_at_post(train, post_to_check=player.town):
                    raise errors.BadCommand('The train is not in Town now, train: {}'.format(train))

            # Upgrade entities:
            for post in posts:
                player.town.armor -= post.next_level_price
                post.set_level(post.level + 1)
                log.info('Post has been upgraded, post: {}'.format(post))
            for train in trains:
                player.town.armor -= train.next_level_price
                train.set_level(train.level + 1)
                log.info('Train has been upgraded, post: {}'.format(train))

    def get_map_layer(self, player, layer):
        """ Returns specified game map layer.
        """
        if layer not in self.map.LAYERS or (layer in CONFIG.HIDDEN_MAP_LAYERS and not self.observed):
            raise errors.ResourceNotFound('Map layer not found, layer: {}'.format(layer))

        log.debug('Load game map layer, layer: {}'.format(layer))
        message = self.map.layer_to_json_str(layer)

        if layer == 1 and not self.observed:
            self.clean_user_events(player)

        return message

    def clean_user_events(self, player):
        """ Cleans all existing event messages for particular user.
        """
        for train in player.trains.values():
            train.events = []
        player.town.events = []

    def update_cooldowns_on_tick(self):
        """ Decreases all cooldown values on game tick.
        """
        # Update cooldowns for random events:
        for event in self.event_cooldowns:
            if self.event_cooldowns[event] != 0:
                self.event_cooldowns[event] = max(self.event_cooldowns[event] - 1, 0)

        # Update cooldowns for trains:
        for train in self.trains.values():
            if train.cooldown != 0:
                train.cooldown = max(train.cooldown - 1, 0)

    def recalculate_ratings_on_tick(self):
        """ Recalculates rating for all players on game tick.
        """
        ratings = self.map.ratings
        for player in self.players.values():
            player.recalculate_rating()
            ratings[player.idx]['rating'] = player.rating

    def retire_events_on_tick(self):
        """ Deletes old event messages and leaves only last event messages.
        """
        for train in self.trains.values():
            train.events = train.events[-CONFIG.MAX_EVENT_MESSAGES:]
        for post in self.map.posts.values():
            post.events = post.events[-CONFIG.MAX_EVENT_MESSAGES:]

    def __del__(self):
        log.info('Game deleted, name: \'{}\''.format(self.name))
