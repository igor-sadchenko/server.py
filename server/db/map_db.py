""" Contains DB helpers for map actions.
"""
import os
from glob import glob

import yaml

from config import CONFIG
from db.models import Base, Map, Line, Point, Post
from db.session import session_wrapper
from logger import log


def reset_db():
    """ Re-applies DB schema.
    """
    Base.metadata.drop_all()
    Base.metadata.create_all()


@session_wrapper
def truncate_tables(session=None):
    """ Truncates all map-related tables.
    """
    tables = [Line.__table__, Post.__table__, Point.__table__, Map.__table__]
    for table in tables:
        session.execute(table.delete())


@session_wrapper
def add_map(size_x, size_y, name='', session=None):
    """ Creates a new Map in DB.
    """
    new_map = Map(name=name, size_x=size_x, size_y=size_y)
    session.add(new_map)
    session.commit()  # Commit to get map's id.
    return new_map.id


@session_wrapper
def add_line(map_id, length, p0, p1, session=None):
    """ Creates a new Line in DB.
    """
    new_line = Line(length=length, p0=p0, p1=p1, map_id=map_id)
    session.add(new_line)
    session.commit()  # Commit to get line's id.
    return new_line.id


@session_wrapper
def add_point(map_id, x=0, y=0, session=None):
    """ Creates a new Point in DB.
    """
    new_point = Point(map_id=map_id, x=x, y=y)
    session.add(new_point)
    session.commit()  # Commit to get point's id.
    return new_point.id


@session_wrapper
def add_post(map_id, point_id, name, type_p, population=0, armor=0, product=0, replenishment=1,
             session=None):
    """ Creates a new Post in DB.
    """
    new_post = Post(name=name, type=type_p, population=population, armor=armor, product=product,
                    replenishment=replenishment, map_id=map_id, point_id=point_id)
    session.add(new_post)
    session.commit()  # Commit to get post's id.
    return new_post.id


def discover_maps(path):
    """ Discovers all available maps files.
    """
    maps = {}
    for f_name in glob(path):
        m_name = os.path.basename(f_name)
        if CONFIG.MAPS_FORMAT:
            m_name = m_name[:-(len(CONFIG.MAPS_FORMAT) + 1)]
        maps[m_name] = f_name
    return maps


@session_wrapper
def set_active_map(map_name, session=None):
    """ Sets specified map as active.
    """
    active_map = session.query(Map).filter(Map.name == map_name).first()

    if active_map is None:
        err_msg = 'Map not found: \'{}\''.format(map_name)
        log.error(err_msg)
        raise ValueError(err_msg)

    session.query(Map).update({'active': False})
    active_map.active = True
    session.add(active_map)


@session_wrapper
def generate_maps(map_names=None, active_map=None, session=None):
    """ Generates a map in DB.
    """
    maps = discover_maps(CONFIG.MAPS_DISCOVERY)
    maps_to_generate = maps.keys() if map_names is None else map_names

    for map_name in maps_to_generate:
        if map_name not in maps:
            err_msg = 'Error, unknown map name: \'{}\', available: {}'.format(map_name, ', '.join(maps.keys()))
            log.error(err_msg)
            raise ValueError(err_msg)

        with open(maps[map_name], 'r') as f:
            m = yaml.load(f)

        # Delete the map if it exist
        session.query(Map).filter(Map.name == m['name']).delete()

        map_id = add_map(name=m['name'], size_x=m['size'][0], size_y=m['size'][1], session=session)

        points_idx = []
        for point in m['points']:
            point_idx = add_point(map_id, x=point[0], y=point[1], session=session)
            points_idx.append(point_idx)

        for post in m['posts']:
            add_post(map_id, points_idx[post.pop('point') - 1], post.pop('name'), post.pop('type'),
                     session=session, **post)

        for line in m['lines']:
            add_line(map_id, line[0], points_idx[line[1] - 1], points_idx[line[2] - 1], session=session)

        log.debug('Map \'{}\' has been generated'.format(map_name))

    if active_map is not None:
        set_active_map(active_map, session=session)


@session_wrapper
def get_map_by_name(map_name, session=None):
    """ Returns map by it's name.
    """
    return session.query(Map).filter(Map.name == map_name).scalar()


@session_wrapper
def get_map_by_id(map_id, session=None):
    """ Returns map by it's ID.
    """
    return session.query(Map).filter(Map.id == map_id).scalar()
