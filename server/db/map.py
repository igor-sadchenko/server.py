""" DB map generator.
"""
import os
from glob import glob
from logging import getLogger

import yaml

from config import CONFIG
from db.models import MapBase, Map, Line, Point, Post
from db.session import map_session_ctx

logger = getLogger('db_map')


def db_session(function):
    def wrapped(*args, **kwargs):
        if kwargs.get('session', None) is None:
            with map_session_ctx() as session:
                kwargs['session'] = session
                return function(*args, **kwargs)
        else:
            return function(*args, **kwargs)
    return wrapped


class DbMap(object):
    """ Contains helpers for map generation.
    """
    def __init__(self):
        self.current_map_id = None

    def reset_db(self):
        """ Re-applies DB schema.
        """
        MapBase.metadata.drop_all()
        MapBase.metadata.create_all()

    @db_session
    def add_map(self, size_x, size_y, name='', session=None):
        """ Creates new Map in DB.
        """
        new_map = Map(name=name, size_x=size_x, size_y=size_y)
        session.add(new_map)
        session.commit()  # Commit to get map's id.
        self.current_map_id = new_map.id
        return self.current_map_id

    @db_session
    def add_line(self, length, p0, p1, map_id=None, session=None):
        """ Creates new Line in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_line = Line(len=length, p0=p0, p1=p1, map_id=_map_id)
        session.add(new_line)
        session.commit()  # Commit to get line's id.
        return new_line.id

    @db_session
    def add_point(self, map_id=None, x=0, y=0, session=None):
        """ Creates new Point in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_point = Point(map_id=_map_id, x=x, y=y)
        session.add(new_point)
        session.commit()  # Commit to get point's id.
        return new_point.id

    @db_session
    def add_post(self, point_id, name, type_p, population=0, armor=0, product=0, replenishment=1, map_id=None,
                 session=None):
        """ Creates new Post in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_post = Post(name=name, type=type_p, population=population, armor=armor, product=product,
                        replenishment=replenishment, map_id=_map_id, point_id=point_id)
        session.add(new_post)
        session.commit()  # Commit to get post's id.
        return new_post.id

    def discover_maps(self, path):
        """ Discovers all available maps files.
        """
        maps = {}
        for f_name in glob(path):
            m_name = os.path.basename(f_name)
            if CONFIG.MAPS_FORMAT:
                m_name = m_name[:-(len(CONFIG.MAPS_FORMAT) + 1)]
            maps[m_name] = f_name
        return maps

    @db_session
    def set_active_map(self, map_name, session=None):
        """ Sets specified map as active.
        """
        active_map = session.query(Map).filter(Map.name == map_name).first()

        if active_map is None:
            err_msg = "Map not found: '{}'".format(map_name)
            logger.error(err_msg)
            raise ValueError(err_msg)

        session.query(Map).update({'active': False})
        active_map.active = True
        session.add(active_map)

    @db_session
    def generate_maps(self, map_names=None, active_map=None, session=None):
        """ Generates 'map.db'.
        """
        maps = self.discover_maps(CONFIG.MAPS_DISCOVERY)
        maps_to_generate = maps.keys() if map_names is None else map_names

        self.reset_db()

        for map_name in maps_to_generate:
            if map_name not in maps:
                err_msg = "Error, unknown map name: '{}', available: {}.".format(map_name, ', '.join(maps.keys()))
                logger.error(err_msg)
                raise ValueError(err_msg)

            with open(maps[map_name], 'r') as f:
                m = yaml.load(f)

            self.add_map(name=m['name'], size_x=m['size'][0], size_y=m['size'][1], session=session)

            point_ids = []
            for point in m['points']:
                point_id = self.add_point(x=point[0], y=point[1], session=session)
                point_ids.append(point_id)

            for post in m['posts']:
                self.add_post(point_ids[post.pop('point') - 1], post.pop('name'), post.pop('type'),
                              session=session, **post)

            for line in m['lines']:
                self.add_line(line[0], point_ids[line[1] - 1], point_ids[line[2] - 1], session=session)

            logger.info("Map '{}' has been generated.".format(map_name))

        if active_map is not None:
            self.set_active_map(active_map, session=session)
