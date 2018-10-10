""" Game map entity.
"""

from sqlalchemy import func
from sqlalchemy.sql.expression import true

import errors
from db.models import Map as MapModel, Line as LineModel, Point as PointModel, Post as PostModel
from db.session import map_session_ctx
from entity.line import Line
from entity.point import Point
from entity.post import Post, PostType
from entity.serializable import Serializable


class Map(Serializable):

    DICT_TO_LIST = ('points', 'lines', 'posts', 'trains', 'coordinates')

    def __init__(self, name=None, use_active=False):
        self.name = name
        self.idx = None
        self.size = (None, None)
        self.lines = {}
        self.points = {}
        self.coordinates = {}
        self.posts = {}
        self.trains = {}
        self.ratings = {}

        # Attributes not included into json representation:
        self.use_active = use_active
        self.initialized = False
        self.markets = []
        self.storages = []
        self.towns = []

        if self.name is not None or self.use_active:
            self.init_map()

    def init_map(self):
        with map_session_ctx() as session:
            if self.name:
                _map = session.query(MapModel).filter(MapModel.name == self.name).first()
            elif self.use_active:
                _map = session.query(MapModel).filter(MapModel.active == true()).first()
            else:
                raise errors.WgForgeServerError('Unable to initialize the map')

            if _map is None:
                raise errors.WgForgeServerError('The map is not found')

            self.idx = _map.id
            self.name = _map.name
            self.size = (_map.size_x, _map.size_y)

            lines = _map.lines.order_by(LineModel.id).all()
            self.lines = {l.id: Line(l.id, l.length, l.p0, l.p1) for l in lines}

            points = session.query(PointModel, func.max(PostModel.id)).outerjoin(
                PostModel, PointModel.id == PostModel.point_id).filter(PointModel.map_id == _map.id).group_by(
                PointModel.id).order_by(PointModel.id).all()
            for point, post_id in points:
                self.coordinates[point.id] = {'idx': point.id, 'x': point.x, 'y': point.y}
                self.points[point.id] = Point(point.id, post_idx=post_id)

            posts = _map.posts.order_by(PostModel.id).all()
            self.posts = {
                p.id: Post(
                    p.id, p.name, p.type, p.population, p.armor, p.product, p.replenishment, p.point_id
                ) for p in posts
            }

            self.markets = [m for m in self.posts.values() if m.type == PostType.MARKET]
            self.storages = [s for s in self.posts.values() if s.type == PostType.STORAGE]
            self.towns = [t for t in self.posts.values() if t.type == PostType.TOWN]

            self.initialized = True

    def add_train(self, train):
        self.trains[train.idx] = train

    def layer_to_json_str(self, layer):
        attributes = ()
        if layer == 0:
            attributes = ('idx', 'name', 'points', 'lines')
        elif layer == 1:
            attributes = ('idx', 'posts', 'trains', 'ratings')
        elif layer == 10:
            attributes = ('idx', 'size', 'coordinates')
        return self.to_json_str(attributes=attributes)

    def __repr__(self):
        return '<Map(idx={}, name={}, lines_idx=[{}], points_idx=[{}], posts_idx=[{}], trains_idx=[{}])>'.format(
            self.idx, self.name,
            ', '.join([str(k) for k in self.lines]),
            ', '.join([str(k) for k in self.points]),
            ', '.join([str(k) for k in self.posts]),
            ', '.join([str(k) for k in self.trains])
        )
