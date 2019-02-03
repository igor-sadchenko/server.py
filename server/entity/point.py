""" Graph vertex - Point entity.
"""
from entity.serializable import Serializable


class Point(Serializable):
    """ Point entity defined by:
    unique id (idx) - index of the point
    post_idx (may be empty) - index of post, defined if a post is associated with the point
    """
    def __init__(self, idx, post_idx=None):
        self.idx = idx
        self.post_idx = post_idx

    def __repr__(self):
        return '<Point(idx={}, post_idx={})>'.format(self.idx, self.post_idx)
